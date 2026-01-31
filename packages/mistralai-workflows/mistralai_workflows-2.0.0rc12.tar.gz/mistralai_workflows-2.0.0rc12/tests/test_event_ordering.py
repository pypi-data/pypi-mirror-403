import asyncio
from unittest.mock import AsyncMock, Mock, call, patch

import pytest

from mistralai_workflows.core.events.event_context import (
    BackgroundEventPublisher,
    EventContext,
)
from mistralai_workflows.core.task.task import Task
from mistralai_workflows.protocol.v1.events import (
    CustomTaskCompleted,
    CustomTaskInProgress,
    CustomTaskStarted,
    WorkflowEvent,
)


def mock_activity_info() -> Mock:
    info = Mock()
    info.workflow_id = "test-workflow-id"
    info.workflow_run_id = "test-run-id"
    info.workflow_type = "test-workflow-type"
    info.activity_id = "test-activity-id"
    info.task_token = b"test-task-token"
    return info


@pytest.fixture
def mock_workflows_client() -> AsyncMock:
    client = AsyncMock()
    client.send_event = AsyncMock(return_value=None)
    return client


@pytest.fixture
async def event_context(mock_workflows_client: AsyncMock) -> EventContext:
    return EventContext(mock_workflows_client)


@pytest.fixture
async def background_publisher(event_context: EventContext) -> BackgroundEventPublisher:
    return BackgroundEventPublisher(event_context)


class TestEventContextSequentialPublishing:
    @pytest.mark.asyncio
    async def test_sequential_publishing_preserves_order(
        self, event_context: EventContext, mock_workflows_client: AsyncMock
    ) -> None:
        events = [
            Mock(spec=WorkflowEvent),
            Mock(spec=WorkflowEvent),
            Mock(spec=WorkflowEvent),
        ]

        async with event_context:
            for event in events:
                await event_context.publish_event(event)

        assert mock_workflows_client.send_event.call_count == 3
        calls = mock_workflows_client.send_event.call_args_list
        assert calls[0] == call(events[0])
        assert calls[1] == call(events[1])
        assert calls[2] == call(events[2])


class TestBackgroundEventPublisherConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_background_tasks_ordered_by_queue(
        self,
        event_context: EventContext,
        background_publisher: BackgroundEventPublisher,
        mock_workflows_client: AsyncMock,
    ) -> None:
        events_sent = []
        send_lock = asyncio.Lock()

        async def track_send(event: WorkflowEvent) -> None:
            await asyncio.sleep(0.01)
            async with send_lock:
                events_sent.append(event)

        mock_workflows_client.send_event = track_send

        async with event_context:
            events = [Mock(spec=WorkflowEvent, name=f"event_{i}") for i in range(5)]

            for event in events:
                background_publisher.publish_event_background(event)

            await background_publisher.drain(timeout=5.0)
            await background_publisher.shutdown()

        assert len(events_sent) == 5
        assert events_sent == events

    @pytest.mark.asyncio
    async def test_drain_waits_for_all_pending_events(
        self,
        event_context: EventContext,
        background_publisher: BackgroundEventPublisher,
        mock_workflows_client: AsyncMock,
    ) -> None:
        slow_send_started = False
        slow_send_finished = False

        async def slow_send(event: WorkflowEvent) -> None:
            nonlocal slow_send_started, slow_send_finished
            slow_send_started = True
            await asyncio.sleep(0.2)
            slow_send_finished = True

        mock_workflows_client.send_event = slow_send

        async with event_context:
            event = Mock(spec=WorkflowEvent)
            background_publisher.publish_event_background(event)

            await background_publisher.drain(timeout=5.0)
            await background_publisher.shutdown()

        assert slow_send_started
        assert slow_send_finished

    @pytest.mark.asyncio
    async def test_multiple_drains_are_safe(
        self,
        event_context: EventContext,
        background_publisher: BackgroundEventPublisher,
        mock_workflows_client: AsyncMock,
    ) -> None:
        async with event_context:
            event = Mock(spec=WorkflowEvent)
            background_publisher.publish_event_background(event)

            await background_publisher.drain(timeout=5.0)
            assert mock_workflows_client.send_event.call_count == 1

            await background_publisher.drain(timeout=5.0)
            assert mock_workflows_client.send_event.call_count == 1

            await background_publisher.shutdown()


class TestTaskEventOrdering:
    @pytest.mark.asyncio
    async def test_task_events_strict_order(
        self,
        event_context: EventContext,
        background_publisher: BackgroundEventPublisher,
        mock_workflows_client: AsyncMock,
    ) -> None:
        events_sent = []

        async def track_send(event: WorkflowEvent) -> None:
            await asyncio.sleep(0.01)
            events_sent.append(event)

        mock_workflows_client.send_event = track_send

        async with event_context:
            with patch(
                "mistralai_workflows.core.task.task.BackgroundEventPublisher.get_current",
                return_value=background_publisher,
            ):
                with patch("mistralai_workflows.core.task.task.temporalio.activity.in_activity", return_value=True):
                    with patch(
                        "mistralai_workflows.core.events.event_utils.temporalio.activity.info",
                        return_value=mock_activity_info(),
                    ):
                        with patch(
                            "mistralai_workflows.core.task.task._should_publish_event",
                            return_value=True,
                        ):
                            task: Task[dict[str, int]] = Task(type="test-task", state={"progress": 0})

                            async with task as t:
                                await t.set_state({"progress": 50})
                                await t.set_state({"progress": 100})

            await background_publisher.drain(timeout=5.0)
            await background_publisher.shutdown()

        assert len(events_sent) == 4
        assert isinstance(events_sent[0], CustomTaskStarted)
        assert isinstance(events_sent[1], CustomTaskInProgress)
        assert isinstance(events_sent[2], CustomTaskInProgress)
        assert isinstance(events_sent[3], CustomTaskCompleted)

    @pytest.mark.asyncio
    async def test_concurrent_tasks_maintain_individual_order(
        self,
        event_context: EventContext,
        background_publisher: BackgroundEventPublisher,
        mock_workflows_client: AsyncMock,
    ) -> None:
        events_sent = []
        send_lock = asyncio.Lock()

        async def track_send(event: WorkflowEvent) -> None:
            await asyncio.sleep(0.01)
            async with send_lock:
                events_sent.append(event)

        mock_workflows_client.send_event = track_send

        async def run_task(task_type: str) -> None:
            with patch(
                "mistralai_workflows.core.task.task.BackgroundEventPublisher.get_current",
                return_value=background_publisher,
            ):
                with patch("mistralai_workflows.core.task.task.temporalio.activity.in_activity", return_value=True):
                    with patch(
                        "mistralai_workflows.core.events.event_utils.temporalio.activity.info",
                        return_value=mock_activity_info(),
                    ):
                        with patch(
                            "mistralai_workflows.core.task.task._should_publish_event",
                            return_value=True,
                        ):
                            task: Task[dict[str, int]] = Task(type=task_type, state={"step": 0})
                            async with task as t:
                                await t.set_state({"step": 1})

        async with event_context:
            await asyncio.gather(run_task("task-A"), run_task("task-B"))
            await background_publisher.drain(timeout=5.0)
            await background_publisher.shutdown()

        assert len(events_sent) == 6

        task_a_events = [e for e in events_sent if getattr(e.attributes, "custom_task_type", None) == "task-A"]
        task_b_events = [e for e in events_sent if getattr(e.attributes, "custom_task_type", None) == "task-B"]

        assert len(task_a_events) == 3
        assert len(task_b_events) == 3

        assert isinstance(task_a_events[0], CustomTaskStarted)
        assert isinstance(task_a_events[1], CustomTaskInProgress)
        assert isinstance(task_a_events[2], CustomTaskCompleted)

        assert isinstance(task_b_events[0], CustomTaskStarted)
        assert isinstance(task_b_events[1], CustomTaskInProgress)
        assert isinstance(task_b_events[2], CustomTaskCompleted)


class TestRaceConditionPrevention:
    @pytest.mark.asyncio
    async def test_custom_task_events_before_activity_completion(
        self,
        event_context: EventContext,
        background_publisher: BackgroundEventPublisher,
        mock_workflows_client: AsyncMock,
    ) -> None:
        events_sent = []

        async def track_send(event: WorkflowEvent) -> None:
            events_sent.append(event)

        mock_workflows_client.send_event = track_send

        async with event_context:
            with patch(
                "mistralai_workflows.core.task.task.BackgroundEventPublisher.get_current",
                return_value=background_publisher,
            ):
                with patch("mistralai_workflows.core.task.task.temporalio.activity.in_activity", return_value=True):
                    with patch(
                        "mistralai_workflows.core.events.event_utils.temporalio.activity.info",
                        return_value=mock_activity_info(),
                    ):
                        with patch(
                            "mistralai_workflows.core.task.task._should_publish_event",
                            return_value=True,
                        ):
                            task: Task[None] = Task(type="test-task")
                            async with task:
                                pass

            await background_publisher.drain(timeout=10.0)
            await background_publisher.shutdown()

            activity_completed_event = Mock(spec=WorkflowEvent, name="ACTIVITY_TASK_COMPLETED")
            await event_context.publish_event(activity_completed_event)

        assert len(events_sent) == 3
        assert isinstance(events_sent[0], CustomTaskStarted)
        assert isinstance(events_sent[1], CustomTaskCompleted)
        assert events_sent[2] is activity_completed_event

    @pytest.mark.asyncio
    async def test_workflow_completion_after_all_activity_events(
        self,
        event_context: EventContext,
        background_publisher: BackgroundEventPublisher,
        mock_workflows_client: AsyncMock,
    ) -> None:
        events_sent = []

        async def track_send(event: WorkflowEvent) -> None:
            events_sent.append(event)

        mock_workflows_client.send_event = track_send

        async with event_context:
            with patch(
                "mistralai_workflows.core.task.task.BackgroundEventPublisher.get_current",
                return_value=background_publisher,
            ):
                with patch("mistralai_workflows.core.task.task.temporalio.activity.in_activity", return_value=True):
                    with patch(
                        "mistralai_workflows.core.events.event_utils.temporalio.activity.info",
                        return_value=mock_activity_info(),
                    ):
                        with patch(
                            "mistralai_workflows.core.task.task._should_publish_event",
                            return_value=True,
                        ):
                            task: Task[None] = Task(type="test-task")
                            async with task:
                                pass

            await background_publisher.drain(timeout=10.0)
            await background_publisher.shutdown()

            activity_completed = Mock(spec=WorkflowEvent, name="ACTIVITY_TASK_COMPLETED")
            await event_context.publish_event(activity_completed)

            workflow_completed = Mock(spec=WorkflowEvent, name="WORKFLOW_EXECUTION_COMPLETED")
            await event_context.publish_event(workflow_completed)

        assert len(events_sent) == 4
        assert isinstance(events_sent[0], CustomTaskStarted)
        assert isinstance(events_sent[1], CustomTaskCompleted)
        assert events_sent[2] is activity_completed
        assert events_sent[3] is workflow_completed


class TestTaskActivityOnlyValidation:
    def test_task_creation_in_activity_succeeds(self) -> None:
        with patch("mistralai_workflows.core.task.task.temporalio.activity.in_activity", return_value=True):
            task: Task[None] = Task(type="test-task")
            assert task.type == "test-task"

    def test_task_creation_in_workflow_succeeds(self) -> None:
        """Tasks can now be used in workflows via local activities."""
        with patch("mistralai_workflows.core.task.task.temporalio.workflow.in_workflow", return_value=True):
            with patch("mistralai_workflows.core.task.task.temporalio.workflow.uuid4", return_value="mock-uuid"):
                task: Task[None] = Task(type="test-task", id="explicit-id")
                assert task.type == "test-task"
                assert task.id == "explicit-id"
