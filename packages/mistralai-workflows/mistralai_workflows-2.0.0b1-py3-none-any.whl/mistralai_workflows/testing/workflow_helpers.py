import asyncio
import json
from typing import Any, cast

import httpx
from pydantic import TypeAdapter

from mistralai_workflows.protocol.v1.events import (
    CustomTaskCompleted,
    CustomTaskInProgress,
    CustomTaskStarted,
    WorkflowEvent,
    WorkflowEventType,
)
from mistralai_workflows.protocol.v1.streaming import StreamEventSsePayload

SSE_DATA_PREFIX = "data:"

sse_payload_adapter: TypeAdapter[StreamEventSsePayload] = TypeAdapter(StreamEventSsePayload)
workflow_event_adapter: TypeAdapter[WorkflowEvent] = TypeAdapter(WorkflowEvent)


async def poll_workflow_status(
    client: httpx.AsyncClient,
    execution_id: str,
    expected_status: str,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    for _ in range(timeout_seconds):
        await asyncio.sleep(1)
        status_response = await client.get(f"/v1/workflows/executions/{execution_id}")
        status_response.raise_for_status()
        status_data = status_response.json()
        status = status_data.get("status")

        if status == expected_status:
            return cast(dict[str, Any], status_data)
        elif status in ["FAILED", "TERMINATED", "TIMED_OUT", "COMPLETED"]:
            if status != expected_status:
                raise RuntimeError(f"Workflow ended with status: {status}, expected: {expected_status}")

    raise TimeoutError(f"Workflow did not reach {expected_status} status within {timeout_seconds}s")


async def poll_pending_inputs(
    client: httpx.AsyncClient,
    execution_id: str,
    expected_count: int = 1,
    timeout_seconds: int = 10,
) -> list[dict[str, Any]]:
    for _ in range(timeout_seconds * 10):
        await asyncio.sleep(0.1)
        try:
            pending_response = await client.post(
                f"/v1/workflows/executions/{execution_id}/queries",
                json={"name": "__get_pending_inputs"},
            )
            pending_response.raise_for_status()
            pending_data = pending_response.json()
            pending_inputs = pending_data.get("result", {}).get("pending_inputs", [])

            if len(pending_inputs) >= expected_count:
                return cast(list[dict[str, Any]], pending_inputs)
        except (httpx.HTTPError, ValueError, KeyError):
            pass

    raise TimeoutError(f"Did not receive {expected_count} pending inputs within {timeout_seconds}s")


async def submit_workflow_update(
    client: httpx.AsyncClient,
    execution_id: str,
    update_name: str,
    update_input: dict[str, Any],
) -> None:
    update_response = await client.post(
        f"/v1/workflows/executions/{execution_id}/updates",
        json={
            "name": update_name,
            "input": update_input,
        },
    )
    update_response.raise_for_status()


async def execute_workflow(client: httpx.AsyncClient, workflow_name: str, input_data: dict[str, Any]) -> str:
    response = await client.post(
        f"/v1/workflows/{workflow_name}/execute",
        json={"input": input_data},
    )
    response.raise_for_status()
    data = response.json()
    execution_id = data.get("execution_id")
    if not execution_id:
        raise ValueError(f"No execution_id returned: {data}")
    return cast(str, execution_id)


async def stream_workflow_events(
    client: httpx.AsyncClient,
    execution_id: str,
    timeout_seconds: float = 30.0,
) -> list[dict[str, Any]]:
    received_events = []
    async with client.stream(
        "GET",
        "/v1/workflows/events/stream",
        params={"workflow_exec_id": execution_id},
        timeout=timeout_seconds,
    ) as stream_response:
        stream_response.raise_for_status()
        async for line in stream_response.aiter_lines():
            if not line or line.startswith(":"):
                continue
            if line.startswith(SSE_DATA_PREFIX):
                event_data = line[len(SSE_DATA_PREFIX) :].strip()
                if event_data:
                    event = json.loads(event_data)
                    sse_payload_adapter.validate_python(event)
                    received_events.append(event)
                    event_type = event.get("data", {}).get("event_type")
                    if event_type == WorkflowEventType.WORKFLOW_EXECUTION_COMPLETED:
                        break
    return received_events


def get_event_types(events: list[dict[str, Any]]) -> list[str]:
    return [e.get("data", {}).get("event_type") for e in events]


def filter_events_by_type(events: list[dict[str, Any]], event_types: list[WorkflowEventType]) -> list[dict[str, Any]]:
    filtered = []
    for e in events:
        event_type = e.get("data", {}).get("event_type")
        if event_type in event_types:
            workflow_event_adapter.validate_python(e.get("data", {}))
            filtered.append(e)
    return filtered


def filter_events_by_custom_task_type(events: list[dict[str, Any]], custom_task_type: str) -> list[dict[str, Any]]:
    filtered = []
    for e in events:
        attrs = e.get("data", {}).get("attributes", {})
        if attrs.get("custom_task_type") == custom_task_type:
            workflow_event_adapter.validate_python(e.get("data", {}))
            filtered.append(e)
    return filtered


def extract_state_from_event(event: dict[str, Any]) -> dict[str, Any] | None:
    validated = sse_payload_adapter.validate_python(event)
    event_data = validated.data
    if isinstance(event_data, (CustomTaskStarted, CustomTaskInProgress, CustomTaskCompleted)):
        payload = event_data.attributes.payload
        if payload.type == "json":
            return cast(dict[str, Any], payload.value)
    return None


def extract_json_patches_from_event(event: dict[str, Any]) -> list[dict[str, Any]]:
    validated = sse_payload_adapter.validate_python(event)
    event_data = validated.data
    if isinstance(event_data, (CustomTaskInProgress, CustomTaskCompleted)):
        payload = event_data.attributes.payload
        if payload.type == "json_patch":
            return [p.model_dump() for p in payload.value]
    return []


async def execute_workflow_and_wait(
    client: httpx.AsyncClient,
    workflow_name: str,
    input_data: dict[str, Any],
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    response = await client.post(
        f"/v1/workflows/{workflow_name}/execute",
        json={"input": input_data},
    )
    response.raise_for_status()
    data = response.json()

    execution_id = data.get("execution_id")
    if not execution_id:
        raise ValueError(f"No execution_id returned: {data}")

    for _ in range(timeout_seconds):
        await asyncio.sleep(1)

        status_response = await client.get(f"/v1/workflows/executions/{execution_id}")
        status_response.raise_for_status()
        status_data = status_response.json()

        status = status_data.get("status")
        if status == "COMPLETED":
            return cast(dict[str, Any], status_data)
        elif status in ["FAILED", "TERMINATED", "TIMED_OUT"]:
            raise RuntimeError(f"Workflow {workflow_name} ended with status: {status}")

    raise TimeoutError(f"Workflow {workflow_name} did not complete within {timeout_seconds}s")
