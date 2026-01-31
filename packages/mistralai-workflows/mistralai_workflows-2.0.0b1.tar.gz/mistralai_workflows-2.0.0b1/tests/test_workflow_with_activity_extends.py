from typing import Any

import pytest

from mistralai_workflows import get_workflow_definition

from .fixtures_activity_extends import (
    ActivityExtendsWorkflow,
    V1Config,
    WorkflowParams,
    process_base,
    process_v1,
    process_v2,
)
from .utils import create_test_worker


class TestActivityExtends:
    @pytest.mark.asyncio
    async def test_extends_decorator_with_temporal_workflow(self, temporal_env: Any) -> None:
        async with create_test_worker(
            temporal_env,
            workflows=[ActivityExtendsWorkflow],
            activities=[process_base, process_v1, process_v2],
        ):
            workflow_def = get_workflow_definition(ActivityExtendsWorkflow)
            assert workflow_def is not None

            params = WorkflowParams(config=V1Config(), data="test")

            handle = await temporal_env.client.start_workflow(
                workflow_def.name,
                params.model_dump(),
                id="test-activity-extends",
                task_queue="test-task-queue",
            )

            result = await handle.result()

            assert result["result"] == "v1: test"
