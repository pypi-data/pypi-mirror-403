import asyncio
from typing import Any, AsyncGenerator, Generator
from unittest.mock import patch

import pytest
import pytest_asyncio
import structlog
from temporalio.testing import WorkflowEnvironment

from mistralai_workflows.core.config.config import config
from mistralai_workflows.core.dependencies.dependency_injector import DependencyInjector

logger = structlog.get_logger(__name__)


@pytest.fixture(scope="session")
def event_loop() -> Generator[Any, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_test_config() -> Generator[None, None, None]:
    original_task_queue = config.temporal.task_queue
    config.temporal.task_queue = "test-task-queue"

    yield

    config.temporal.task_queue = original_task_queue


@pytest.fixture(autouse=True)
def clear_dependency_cache() -> Generator[None, None, None]:
    """Clear resolved dependencies between tests to prevent state leakage."""
    yield
    DependencyInjector.clear_resolved_dependencies()


@pytest.fixture(autouse=True)
def mock_upsert_search_attributes() -> Generator[Any, None, None]:
    """Mock upsert_search_attributes for test environment.

    Test environments don't have custom search attributes defined,
    so we mock this function to avoid errors during testing.
    """
    with patch("mistralai_workflows.core.tracing.utils.temporalio.workflow.upsert_search_attributes") as mock:
        yield mock


@pytest_asyncio.fixture
async def temporal_env() -> AsyncGenerator[WorkflowEnvironment, None]:
    """Create a Temporal test environment with time-skipping support.

    This provides an isolated, in-memory Temporal environment for testing
    without requiring a running Temporal server.
    """
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env
