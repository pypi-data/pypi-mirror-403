import asyncio
from contextvars import ContextVar, Token
from typing import Any, Optional

import structlog

from mistralai_workflows.client import WorkflowsClient
from mistralai_workflows.core.utils.contextvars import reset_contextvar
from mistralai_workflows.protocol.v1.events import WorkflowEvent

logger = structlog.get_logger(__name__)

# PROBLEM: We want to publish events to the Workflows API from within Temporal workflows, but Temporal
# sandboxes workflows from asyncio (no event loop access, no IO) to enforce deterministic replay.
#
# SOLUTION: Store an EventContext (WorkflowsClient) as a global singleton, created by the
# main worker before running workflows. Workflows/activities call `EventContext.get_singleton().publish_event()`
# which executes IO on the worker's asyncio loop—outside Temporal's sandbox.
#
# WHY GLOBAL (not contextvars)? Temporal clears contextvars between workflow/activity boundaries.
# The contextvar `_is_event_context_singleton_owner` only tracks who created the singleton for cleanup.
_event_context_singleton: Optional["EventContext"] = None
_is_event_context_singleton_owner: ContextVar[bool] = ContextVar("is_event_context_singleton_owner", default=False)

# Activity-scoped background event publisher for custom task events (streaming)
_background_event_publisher: ContextVar[Optional["BackgroundEventPublisher"]] = ContextVar(
    "background_event_publisher", default=None
)


class EventContext:
    """Context for publishing workflow and activity lifecycle events sequentially.

    Used by workflow/activity interceptors to send lifecycle events (STARTED, COMPLETED, etc.).
    Events are sent synchronously to guarantee ordering.
    """

    def __init__(self, workflows_client: WorkflowsClient):
        self.workflows_client = workflows_client
        self._token: Optional[Token] = None

    @staticmethod
    def get_singleton() -> Optional["EventContext"]:
        """Get the current event context singleton."""
        return _event_context_singleton

    async def __aenter__(self) -> "EventContext":
        """Enter the event context, setting it as the singleton."""
        global _event_context_singleton
        if _event_context_singleton is not None:
            return _event_context_singleton

        self._token = _is_event_context_singleton_owner.set(True)
        _event_context_singleton = self
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the event context, cleaning up resources."""
        global _event_context_singleton
        if not _is_event_context_singleton_owner.get():
            return

        assert self._token, "Should have token because _is_event_context_singleton_owner is True"
        reset_contextvar(_is_event_context_singleton_owner, self._token)
        _event_context_singleton = None

    async def publish_event(self, event: WorkflowEvent) -> None:
        if self._token is None:
            raise RuntimeError("EventContext not entered")

        try:
            await self.workflows_client.send_event(event)
        except Exception as e:
            logger.warning(
                "Failed to send workflow event",
                event_type=event.event_type,
                error=str(e),
            )


class BackgroundEventPublisher:
    """Handles background publishing of custom task events (streaming) within an activity.

    Custom task events are sent via a FIFO queue to guarantee strict ordering.
    A single background sender task processes events sequentially.
    The activity interceptor waits for the queue to drain before marking the activity as complete.
    """

    def __init__(self, event_context: EventContext):
        self.event_context = event_context
        self._event_queue: asyncio.Queue[Optional[WorkflowEvent]] = asyncio.Queue()
        self._sender_task: Optional[asyncio.Task] = None

    @staticmethod
    def get_current() -> Optional["BackgroundEventPublisher"]:
        return _background_event_publisher.get()

    @staticmethod
    def set_current(publisher: Optional["BackgroundEventPublisher"]) -> Token:
        return _background_event_publisher.set(publisher)

    async def _event_sender_loop(self) -> None:
        while True:
            event = await self._event_queue.get()
            if event is None:  # Sentinel value for shutdown
                self._event_queue.task_done()
                break
            try:
                await self.event_context.publish_event(event)
            except Exception as e:
                logger.error(
                    "Failed to send event from background queue",
                    event_type=event.event_type,
                    error=str(e),
                )
            finally:
                self._event_queue.task_done()

    def publish_event_background(self, event: WorkflowEvent) -> None:
        """Publish a custom task event to the background queue for streaming.

        Events are processed in strict FIFO order by a single background sender task.
        The activity interceptor ensures all queued events are sent before completion.
        """
        if self._sender_task is None:
            self._sender_task = asyncio.create_task(self._event_sender_loop())
        self._event_queue.put_nowait(event)

    async def drain(self, timeout: float = 10.0) -> None:
        """Wait for all queued events to be sent."""
        try:
            await asyncio.wait_for(self._event_queue.join(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(
                "Timeout waiting for event queue to drain",
                pending_count=self._event_queue.qsize(),
                timeout=timeout,
            )
        except Exception as e:
            logger.error(
                "Error waiting for event queue to drain",
                error=str(e),
            )

    async def shutdown(self) -> None:
        if self._sender_task is None:
            return

        # Send sentinel value to stop the sender loop
        self._event_queue.put_nowait(None)

        try:
            await asyncio.wait_for(self._sender_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for event sender task to shutdown")
            self._sender_task.cancel()
            try:
                await self._sender_task
            except asyncio.CancelledError:
                pass
        except Exception as e:
            logger.error("Error shutting down event sender task", error=str(e))
        finally:
            self._sender_task = None
