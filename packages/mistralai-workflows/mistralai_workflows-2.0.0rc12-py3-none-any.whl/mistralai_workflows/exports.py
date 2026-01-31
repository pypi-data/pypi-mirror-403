from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _get_version

from .client import WorkflowsClient
from .core.activity import activity
from .core.config.config import AppConfig as WorkflowsConfig
from .core.config.config import config
from .core.definition.workflow_definition import get_workflow_definition
from .core.dependencies.dependency_injector import DependencyInjector, Depends
from .core.execution.concurrency import (
    ExtraItemParams,
    GetItemFromIndexParams,
    execute_activities_in_parallel,
)
from .core.execution.local_activity import run_activities_locally
from .core.execution.sticky_session.get_sticky_worker_session import (
    get_sticky_worker_session,
)
from .core.execution.sticky_session.run_sticky_worker_session import (
    run_sticky_worker_session,
)
from .core.execution.sticky_session.sticky_worker_session import StickyWorkerSession
from .core.execution.workflow_execution import execute_workflow, get_execution_id
from .core.interactive_workflow import InteractiveWorkflow
from .core.rate_limiting.rate_limit import RateLimit
from .core.task import task, task_from
from .core.worker import run_worker
from .core.workflow import workflow
from .exceptions import ActivityError, WorkflowError
from .models import (
    ScheduleCalendar,
    ScheduleInterval,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleRange,
)
from .models import (
    ScheduleDefinition as Schedule,
)

try:
    __version__ = _get_version("mistralai-workflows")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

__all__ = [
    "__version__",
    "activity",
    "run_worker",
    "workflow",
    "get_workflow_definition",
    "execute_workflow",
    "get_execution_id",
    "InteractiveWorkflow",
    "WorkflowsConfig",
    "config",
    "Depends",
    "DependencyInjector",
    "WorkflowsClient",
    "WorkflowError",
    "ActivityError",
    "Schedule",
    "ScheduleCalendar",
    "ScheduleInterval",
    "ScheduleOverlapPolicy",
    "SchedulePolicy",
    "ScheduleRange",
    "ExtraItemParams",
    "execute_activities_in_parallel",
    "GetItemFromIndexParams",
    "run_sticky_worker_session",
    "get_sticky_worker_session",
    "StickyWorkerSession",
    "run_activities_locally",
    "RateLimit",
    "task",
    "task_from",
]
