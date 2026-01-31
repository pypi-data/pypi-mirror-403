import asyncio
import contextvars
import inspect
from contextlib import AsyncExitStack, asynccontextmanager
from functools import cache, wraps
from typing import (
    Any,
    AsyncContextManager,
    AsyncGenerator,
    Callable,
    ContextManager,
    Dict,
    Generator,
    List,
    TypeVar,
    cast,
)

T = TypeVar("T")
U = TypeVar("U", bound=Callable[..., Any])


class DependsCls:
    def __init__(self, dependency: Callable):
        self.dependency = dependency


def Depends(dependency: Any) -> Any:
    return DependsCls(dependency)


class DependencyInjector:
    def __init__(self) -> None:
        self._dependencies_ctx: Dict[Callable, Callable[..., AsyncContextManager]] = {}
        self._dependencies_values: contextvars.ContextVar[Dict[Callable, Any] | None] = contextvars.ContextVar(
            "dependencies_ctx", default=None
        )

    def _register(self, dependency: Callable) -> None:
        if dependency in self._dependencies_ctx:
            return

        # We use a wrapper to handle sync function, sync context manager, async function and async context manager
        # in a unified way
        @asynccontextmanager
        async def async_context_manager_wrapper() -> AsyncGenerator[Any, None]:
            result = dependency()
            if isinstance(result, AsyncContextManager):
                async with result as value:
                    yield value
            elif isinstance(result, ContextManager):
                with result as value:
                    yield value
            elif isinstance(result, AsyncGenerator):
                async for value in result:
                    yield value
            elif isinstance(result, Generator):
                for value in result:
                    yield value
            elif asyncio.iscoroutine(result):
                yield await result
            else:
                yield result

        self._dependencies_ctx[dependency] = async_context_manager_wrapper

    def auto_resolve_dependencies(self, func: U) -> U:
        """Automatically resolve dependencies for a function.

        Args:
            func (U): The function to resolve dependencies for.

        Returns:
            U: The function with dependencies resolved.
        """

        # Get function arguments
        sig = inspect.signature(func)
        parameters = sig.parameters

        # Collect dependencies for each parameter
        provided_kwargs: Dict[str, Callable] = {}
        for param_name, param in parameters.items():
            if isinstance(param.default, DependsCls):
                # Register and resolve dependency
                provided_kwargs[param_name] = param.default.dependency
                self._register(param.default.dependency)

        def resolve_kwargs(kwargs: Dict[str, Any]) -> None:
            # Resolve all the dependencies with the resolved values
            dependency_injector = DependencyInjector.get_singleton_instance()
            dependencies_values = dependency_injector._dependencies_values.get()
            assert not provided_kwargs or dependencies_values is not None, (
                "Please ensure worker is running inside context `async with dependency_injector.with_dependencies()``"
            )
            dependencies_values = dependencies_values or {}
            for kwarg_name, dependency in provided_kwargs.items():
                kwargs[kwarg_name] = dependencies_values[dependency]

        @wraps(func)
        async def async_wrapper_method(*args: List[Any], **kwargs: Dict[str, Any]) -> Any:
            resolve_kwargs(kwargs)
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper_method(*args: List[Any], **kwargs: Dict[str, Any]) -> Any:
            resolve_kwargs(kwargs)
            return func(*args, **kwargs)

        wrapper_method = cast(U, async_wrapper_method if asyncio.iscoroutinefunction(func) else sync_wrapper_method)

        # Remove the injected dependencies from the signature
        sig = inspect.signature(wrapper_method)
        params = [p for name, p in sig.parameters.items() if name not in provided_kwargs]
        wrapper_method.__signature__ = sig.replace(parameters=params)  # type: ignore[attr-defined]
        wrapper_method.__annotations__ = {
            name: annotation
            for name, annotation in wrapper_method.__annotations__.items()
            if name not in provided_kwargs
        }

        return wrapper_method

    @asynccontextmanager
    async def with_dependencies(self) -> AsyncGenerator[None, None]:
        async with AsyncExitStack() as stack:
            try:
                # Clear the dependencies values
                self._dependencies_values.set({})
                items = self._dependencies_ctx.items()
                contexts = [ctx() for _, ctx in items]
                coroutines = [stack.enter_async_context(ctx) for ctx in contexts]
                # Resolve all the dependencies concurrently
                values = await asyncio.gather(*coroutines)
                self._dependencies_values.set({callable: value for (callable, _), value in zip(items, values)})

                yield
            finally:
                self._dependencies_values.set(None)

    @cache
    @staticmethod
    def get_singleton_instance() -> "DependencyInjector":
        return DependencyInjector()

    @staticmethod
    def clear_singleton_cache() -> None:
        """Clear the singleton cache. Useful for testing."""
        DependencyInjector.get_singleton_instance.cache_clear()

    @staticmethod
    def clear_resolved_dependencies() -> None:
        """Clear only the resolved dependency values, keeping registrations. Useful for testing."""
        instance = DependencyInjector.get_singleton_instance()
        instance._dependencies_values.set(None)

    @staticmethod
    def snapshot_dependencies() -> Dict[Callable, Callable[..., AsyncContextManager]]:
        """Capture current dependency registrations. Useful for testing."""
        instance = DependencyInjector.get_singleton_instance()
        return instance._dependencies_ctx.copy()

    @staticmethod
    def restore_dependencies(snapshot: Dict[Callable, Callable[..., AsyncContextManager]]) -> None:
        """Restore dependency registrations to a previous state. Useful for testing."""
        instance = DependencyInjector.get_singleton_instance()
        instance._dependencies_ctx = snapshot.copy()
        instance._dependencies_values.set(None)  # Clear resolved values too

    @staticmethod
    def is_inside_dependencies_context() -> bool:
        """Check if the current execution is inside the with_dependencies context.

        Returns:
            bool: True if inside the with_dependencies context, False otherwise.
        """
        return DependencyInjector.get_singleton_instance()._dependencies_values.get() is not None
