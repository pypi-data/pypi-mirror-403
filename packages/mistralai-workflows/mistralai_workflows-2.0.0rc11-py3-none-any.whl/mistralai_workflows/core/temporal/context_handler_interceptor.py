from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Sequence, Tuple, Type

import structlog
import temporalio.client
import temporalio.worker
import temporalio.workflow
from pydantic_core import from_json, to_json
from temporalio import workflow

from mistralai_workflows.core.utils.contextvars import reset_contextvar
from mistralai_workflows.models import PayloadWithContext, WorkflowContext

logger = structlog.get_logger(__name__)

workflow_context_var: ContextVar[str | None] = ContextVar("workflow_context", default=None)


def unwrap_contextual_args(args: Sequence[Any]) -> Tuple[WorkflowContext | None, Sequence[Any]]:
    """Unwrap contextual args (PayloadWithContext), return the workflow context and the unwrapped args"""
    workflow_context: WorkflowContext | None = None
    new_args_list = []

    for arg in args:
        if isinstance(arg, PayloadWithContext):
            workflow_context = arg.context
            if not arg.empty:
                payload = arg.payload
                # Only try to parse as JSON if it's a JSON string (starts with { or [)
                # For primitive types that are already deserialized, use them directly
                if isinstance(payload, str) and (payload.startswith("{") or payload.startswith("[")):
                    new_args_list.append(from_json(payload))
                elif isinstance(payload, (bytes, bytearray)):
                    new_args_list.append(from_json(payload))
                else:
                    # Payload is already deserialized (primitive type or object)
                    new_args_list.append(payload)
        else:
            new_args_list.append(arg)

    return workflow_context, new_args_list


def wrap_result_with_context(result: Any, workflow_context: WorkflowContext | None) -> Any:
    """Wrap result with workflow context if it exists"""
    if workflow_context is None:
        return result
    return PayloadWithContext(payload=to_json(result), context=workflow_context)


@contextmanager
def define_context(workflow_context: WorkflowContext | None) -> Any:
    """Set workflow context in contextvar for later use"""
    token = workflow_context_var.set(workflow_context.model_dump_json()) if workflow_context else None
    try:
        yield
    finally:
        if token:
            reset_contextvar(workflow_context_var, token)


def retrieve_context() -> WorkflowContext | None:
    """Extract workflow context from contextvar"""
    context_json = workflow_context_var.get()
    if context_json is not None:
        return WorkflowContext.model_validate_json(context_json)
    return None


def create_workflow_context() -> WorkflowContext:
    """Create WorkflowContext from workflow.info() - single source of truth for identity."""
    workflow_info = workflow.info()
    logger.debug(
        "create_workflow_context called",
        workflow_id=workflow_info.workflow_id,
        workflow_type=workflow_info.workflow_type,
        parent_workflow_id=workflow_info.parent.workflow_id if workflow_info.parent else None,
        root_workflow_id=workflow_info.root.workflow_id if workflow_info.root else None,
    )
    return WorkflowContext(
        namespace=workflow_info.namespace,
        execution_id=workflow_info.workflow_id,
        root_workflow_exec_id=workflow_info.root.workflow_id if workflow_info.root else None,
        parent_workflow_exec_id=workflow_info.parent.workflow_id if workflow_info.parent else None,
    )


class WorkflowContextWorkflowOutboundInterceptor(temporalio.worker.WorkflowOutboundInterceptor):
    def _contextualize_args(self, args: Sequence[Any]) -> Sequence[Any]:
        workflow_context = retrieve_context()
        if workflow_context:
            contextualized_args = []
            for arg in args:
                contextualized_args.append(PayloadWithContext(payload=to_json(arg), context=workflow_context))
            if len(contextualized_args) == 0:
                contextualized_args.append(PayloadWithContext(payload=b"null", empty=True, context=workflow_context))
            return contextualized_args
        return args

    async def signal_child_workflow(self, input: temporalio.worker.SignalChildWorkflowInput) -> None:
        input.args = self._contextualize_args(input.args)
        await self.next.signal_child_workflow(input)

    async def signal_external_workflow(self, input: temporalio.worker.SignalExternalWorkflowInput) -> None:
        input.args = self._contextualize_args(input.args)
        await self.next.signal_external_workflow(input)

    def start_activity(self, input: temporalio.worker.StartActivityInput) -> temporalio.workflow.ActivityHandle:
        input.args = self._contextualize_args(input.args)
        return self.next.start_activity(input)

    async def start_child_workflow(
        self, input: temporalio.worker.StartChildWorkflowInput
    ) -> temporalio.workflow.ChildWorkflowHandle:
        input.args = self._contextualize_args(input.args)
        return await self.next.start_child_workflow(input)

    def start_local_activity(
        self, input: temporalio.worker.StartLocalActivityInput
    ) -> temporalio.workflow.ActivityHandle:
        input.args = self._contextualize_args(input.args)
        return self.next.start_local_activity(input)


class WorkflowContextWorkflowInboundInterceptor(temporalio.worker.WorkflowInboundInterceptor):
    """Handles context creation and PayloadWithContext wrapping/unwrapping.

    This interceptor:
    1. Creates fresh WorkflowContext for every workflow from workflow.info()
    2. Sets context in contextvar for activities and streaming to access
    3. Wraps/unwraps PayloadWithContext for cross-worker context propagation
    """

    def init(self, outbound: temporalio.worker.WorkflowOutboundInterceptor) -> None:
        self.next.init(WorkflowContextWorkflowOutboundInterceptor(outbound))

    async def execute_workflow(self, input: temporalio.worker.ExecuteWorkflowInput) -> Any:
        # Create fresh context from workflow.info() - single source of truth for identity
        workflow_context = create_workflow_context()

        logger.debug(
            "Created workflow context",
            workflow_id=workflow_context.execution_id,
            parent_workflow_id=workflow_context.parent_workflow_exec_id,
            root_workflow_id=workflow_context.root_workflow_exec_id,
            is_child_workflow=workflow_context.parent_workflow_exec_id is not None,
        )

        # Unwrap args - discard any context from parent (we use fresh context)
        _, input.args = unwrap_contextual_args(input.args)

        # Execute with context set for activities and streaming
        with define_context(workflow_context):
            # result = await self.next.execute_workflow(input)
            result = await super().execute_workflow(input)
        # Wrap result for proper codec encoding (required for encryption to work correctly)
        return wrap_result_with_context(result, workflow_context)
        # return result

    async def handle_signal(self, input: temporalio.worker.HandleSignalInput) -> None:
        """Called to handle a signal."""
        _, input.args = unwrap_contextual_args(input.args)
        workflow_context = create_workflow_context()
        with define_context(workflow_context):
            await self.next.handle_signal(input)

    async def handle_query(self, input: temporalio.worker.HandleQueryInput) -> Any:
        """Called to handle a query."""
        _, input.args = unwrap_contextual_args(input.args)
        workflow_context = create_workflow_context()
        with define_context(workflow_context):
            result = await self.next.handle_query(input)
        return wrap_result_with_context(result, workflow_context)

    def handle_update_validator(self, input: temporalio.worker.HandleUpdateInput) -> None:
        _, input.args = unwrap_contextual_args(input.args)
        workflow_context = create_workflow_context()
        with define_context(workflow_context):
            self.next.handle_update_validator(input)

    async def handle_update_handler(self, input: temporalio.worker.HandleUpdateInput) -> Any:
        _, input.args = unwrap_contextual_args(input.args)
        workflow_context = create_workflow_context()
        with define_context(workflow_context):
            result = await self.next.handle_update_handler(input)
        return wrap_result_with_context(result, workflow_context)


class WorkflowContextActivityInboundInterceptor(temporalio.worker.ActivityInboundInterceptor):
    """Inbound interceptors runs in the workflow context"""

    async def execute_activity(self, input: temporalio.worker.ExecuteActivityInput) -> Any:
        workflow_context, input.args = unwrap_contextual_args(input.args)
        with define_context(workflow_context):
            result = await self.next.execute_activity(input)
        return wrap_result_with_context(result, workflow_context)


class ContextHandlerInterceptor(temporalio.client.Interceptor, temporalio.worker.Interceptor):
    def intercept_client(self, next: temporalio.client.OutboundInterceptor) -> temporalio.client.OutboundInterceptor:
        return next

    def intercept_activity(
        self, next: temporalio.worker.ActivityInboundInterceptor
    ) -> temporalio.worker.ActivityInboundInterceptor:
        return WorkflowContextActivityInboundInterceptor(next)

    def workflow_interceptor_class(
        self, input: temporalio.worker.WorkflowInterceptorClassInput
    ) -> Type[temporalio.worker.WorkflowInboundInterceptor] | None:
        return WorkflowContextWorkflowInboundInterceptor
