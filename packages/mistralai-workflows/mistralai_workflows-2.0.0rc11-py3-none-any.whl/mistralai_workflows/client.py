import asyncio
import http
import uuid
from typing import Any, AsyncGenerator, Dict, TypeVar

import httpx
import orjson
import structlog
from pydantic import BaseModel

from mistralai_workflows.core.config.config import config
from mistralai_workflows.core.encoding.payload_encoder import PayloadEncoder
from mistralai_workflows.core.utils.id_generator import generate_two_part_id
from mistralai_workflows.exceptions import ErrorCode, WorkflowsException
from mistralai_workflows.models import (
    NetworkEncodedInput,
    ScheduleDefinition,
    WorkflowContext,
    WorkflowSpecWithTaskQueue,
)
from mistralai_workflows.protocol.v1.events import (
    WorkflowEvent,
    WorkflowEventRequest,
    WorkflowEventResponse,
)
from mistralai_workflows.protocol.v1.streaming import (
    PublishStreamEventRequest,
    PublishStreamEventResponse,
    StreamEvent,
    StreamEventsQueryParams,
)
from mistralai_workflows.protocol.v1.worker import WorkerInfo
from mistralai_workflows.protocol.v1.workflow import (
    QueryInvocationBody,
    QueryWorkflowResponse,
    ResetInvocationBody,
    SignalInvocationBody,
    SignalWorkflowResponse,
    TerminateWorkflowRequest,
    UpdateInvocationBody,
    UpdateWorkflowResponse,
    WorkflowExecutionListResponse,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowExecutionStatus,
    WorkflowExecutionSyncResponse,
    WorkflowExecutionTraceEventsResponse,
    WorkflowExecutionTraceSummaryResponse,
    WorkflowExecutionTracOTelResponse,
    WorkflowGetResponse,
    WorkflowListResponse,
    WorkflowScheduleListResponse,
    WorkflowScheduleRequest,
    WorkflowScheduleResponse,
    WorkflowSpecsRegisterRequest,
    WorkflowSpecsRegisterResponse,
    WorkflowVersionListResponse,
)

logger = structlog.get_logger(__name__)

ResponseType = TypeVar(
    "ResponseType",
    WorkflowExecutionResponse,
    WorkflowExecutionSyncResponse,
    QueryWorkflowResponse,
    UpdateWorkflowResponse,
)

SCHEDULE_CORRELATION_ID_PLACEHOLDER = "__scheduled_workflow__"


class WorkflowsClient:
    """Client for interacting with the Workflows API."""

    _scheduler_namespace: str | None = None

    def __init__(
        self,
        base_url: str,
        api_version: str = "v1",
        timeout: float = 60.0,
        api_key: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """
        Args:
            base_url: The base URL of the Workflows API.
            api_version: The API version to use.
            timeout: The timeout for API requests in seconds.
            api_key: Optional API key for authentication (sent as Bearer token).
        """
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.timeout = timeout
        self.api_key = api_key

        self.payload_encoder = PayloadEncoder(
            offloading_config=config.worker.temporal_payload_offloading,
            encryption_config=config.worker.temporal_payload_encryption,
        )
        if headers is None:
            headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.client = httpx.AsyncClient(timeout=timeout, verify=config.common.ca_bundle or True, headers=headers)
        self.api_url = f"{self.base_url}/{self.api_version}/workflows"
        logger.debug(
            "Initialized WorkflowsClient",
            api_url=self.api_url,
            timeout=self.timeout,
            api_key=api_key,
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "WorkflowsClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def _serialize_data_to_json(self, data: Any | None) -> bytes | None:
        """Serialize data to JSON bytes using orjson, with Pydantic support."""
        if data is None:
            return None

        def orjson_default(obj: Any) -> Any:
            if isinstance(obj, BaseModel):
                return obj.model_dump(mode="json")
            raise WorkflowsException(
                code=ErrorCode.UNSERIALIZABLE_PAYLOAD_ERROR,
                message=f"Type {type(obj).__name__} not serializable",
                status=http.HTTPStatus.UNPROCESSABLE_ENTITY,
            )

        if isinstance(data, BaseModel):
            python_data = data.model_dump(serialize_as_any=True)
            return orjson.dumps(python_data, default=orjson_default)
        else:
            return orjson.dumps(data, default=orjson_default)

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] | None = None,
        data: Dict[str, Any] | BaseModel | None = None,
    ) -> httpx.Response:
        """Make a request to the Workflows API.

        Args:
            method: The HTTP method to use.
            endpoint: The API endpoint to request.
            params: Optional query parameters.
            data: Optional request body.

        Returns:
            The HTTP response.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        url = f"{self.api_url}{endpoint}"

        # Convert Pydantic models to dict
        json_data: bytes | None = self._serialize_data_to_json(data)

        logger.debug(
            "Making request to Workflows API",
            method=method,
            url=url,
            params=params,
            json_data=json_data,
        )

        if method.upper() == "GET":
            response = await self.client.get(url, params=params)
        elif method.upper() == "POST":
            response = await self.client.post(
                url, params=params, content=json_data, headers={"Content-Type": "application/json"}
            )
        elif method.upper() == "DELETE":
            response = await self.client.delete(url, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        if response.status_code >= 400:
            logger.error(response.content)

        response.raise_for_status()

        return response

    async def _decode_response(self, response: ResponseType) -> ResponseType:
        if response.result and self.payload_encoder and self.payload_encoder.check_is_payload_encoded(response.result):
            response.result = await self.payload_encoder.decode_network_result(response.result)
        return response

    async def publish_stream_event(self, event: StreamEvent) -> int:
        try:
            response = await self._request(
                "POST", "/executions/stream", data=PublishStreamEventRequest(event=event).model_dump()
            )
            response.raise_for_status()
            ack = PublishStreamEventResponse.model_validate(response.json())
            return ack.broker_sequence
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to publish stream event", code=ErrorCode.POST_EXECUTIONS_STREAM_ERROR
            ) from exc

    async def stream_events(self, params: StreamEventsQueryParams) -> AsyncGenerator[StreamEvent, None]:
        """Stream workflow/activity events as SSE and yield parsed events."""
        endpoint = "/events/stream"
        query = params.model_dump(exclude_none=True)
        try:
            async with self.client.stream("GET", f"{self.api_url}{endpoint}", params=query) as response:
                response.raise_for_status()

                event_type: str | None = None
                async for line in response.aiter_lines():
                    if line is None or line == "" or line.startswith(":"):
                        continue

                    if line.startswith("event:"):
                        event_type = line[len("event:") :].strip()
                        continue

                    if line.startswith("data:"):
                        raw_data = line[len("data:") :].strip()
                        try:
                            parsed = orjson.loads(raw_data)

                            # Handle error events from server
                            if event_type == "error" or (isinstance(parsed, dict) and "error" in parsed):
                                if isinstance(parsed, dict):
                                    error_msg = parsed.get("error", "Unknown stream error")
                                else:
                                    error_msg = str(parsed)
                                raise WorkflowsException(
                                    message=f"Stream error from server: {error_msg}",
                                    code=ErrorCode.GET_EVENTS_STREAM_ERROR,
                                )

                            yield StreamEvent.model_validate(parsed)
                        except WorkflowsException:
                            raise
                        except Exception as e:
                            logger.warning("Failed to parse SSE payload", error=str(e), raw_data=raw_data)
                        finally:
                            event_type = None  # Reset for next event
        except WorkflowsException:
            raise
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to stream events", code=ErrorCode.GET_EVENTS_STREAM_ERROR
            ) from exc

    async def get_workflows(
        self,
        active_only: bool = True,
        limit: int | None = None,
        cursor: uuid.UUID | None = None,
    ) -> WorkflowListResponse:
        """Get workflows."""
        params: dict[str, Any] = {}
        if active_only:
            params["active_only"] = active_only
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        try:
            response = await self._request("GET", "", params=params)
            return WorkflowListResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to get workflows", code=ErrorCode.GET_WORKFLOWS_ERROR
            ) from exc

    async def get_workflow_versions(
        self,
        workflow_name: str | None = None,
        workflow_id: uuid.UUID | None = None,
        active_only: bool = True,
        with_workflow: bool = False,
        limit: int | None = None,
        cursor: uuid.UUID | None = None,
    ) -> WorkflowVersionListResponse:
        """List workflow versions."""
        params: dict[str, Any] = {}
        if workflow_name:
            params["workflow_name"] = workflow_name
        if workflow_id:
            params["workflow_id"] = workflow_id
        if active_only:
            params["active_only"] = active_only
        if with_workflow:
            params["with_workflow"] = with_workflow
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        try:
            response = await self._request("GET", "/versions", params=params)
            return WorkflowVersionListResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to get workflow versions", code=ErrorCode.GET_WORKFLOWS_VERSIONS_ERROR
            ) from exc

    async def get_scheduler_namespace(self) -> str:
        try:
            if not self._scheduler_namespace:
                self._scheduler_namespace = (await self.who_am_i()).namespace
            return self._scheduler_namespace
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to get scheduler namespace", code=ErrorCode.GET_WORKERS_WHOAMI_ERROR
            ) from exc

    async def who_am_i(self) -> WorkerInfo:
        try:
            response = await self._request("GET", "/workers/whoami")
            return WorkerInfo.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to get worker info", code=ErrorCode.GET_WORKERS_WHOAMI_ERROR
            ) from exc

    async def get_workflow(self, workflow_identifier: str | uuid.UUID) -> WorkflowGetResponse:
        """Get a workflow definition by name or ID."""
        try:
            response = await self._request("GET", f"/{workflow_identifier}")
            return WorkflowGetResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to get workflow", code=ErrorCode.GET_WORKFLOWS_ERROR
            ) from exc

    async def register_workflow_specs(
        self,
        definitions: list[WorkflowSpecWithTaskQueue],
    ) -> WorkflowSpecsRegisterResponse:
        """Register workflow specs.

        Args:
            definitions: The workflow specs to register.
        """
        try:
            request = WorkflowSpecsRegisterRequest(definitions=definitions)
            response = await self._request("POST", "/register", data=request)
            return WorkflowSpecsRegisterResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to register workflow specs", code=ErrorCode.POST_WORKFLOWS_REGISTER_ERROR
            ) from exc

    async def execute_workflow(
        self,
        workflow_identifier: str,
        input_data: BaseModel | None,
        execution_id: str | None = None,
        task_queue: str | None = None,
        wait_for_result: bool = False,
        timeout_seconds: float | None = None,
        custom_tracing_attributes: dict[str, str] | None = None,
    ) -> WorkflowExecutionResponse | WorkflowExecutionSyncResponse:
        """Execute a workflow.

        Args:
            workflow_identifier: The workflow name or ID.
            execution_request: The execution request.

        Returns:
            The workflow execution response. If execution_request.wait_for_result is True,
            returns a WorkflowExecutionSyncResponse with the result, otherwise returns
            a WorkflowExecutionResponse.
        """
        try:
            if not execution_id:
                execution_id = generate_two_part_id(workflow_identifier)

            input_data_dict = input_data.model_dump(mode="json") if input_data else {}

            encoded_input = await self._encode_input_if_needed(execution_id=execution_id, input_data=input_data_dict)
            response = await self._request(
                "POST",
                f"/{workflow_identifier}/execute",
                data=WorkflowExecutionRequest(
                    execution_id=execution_id,
                    wait_for_result=wait_for_result,
                    timeout_seconds=timeout_seconds,
                    input=encoded_input,
                    custom_tracing_attributes=custom_tracing_attributes,
                    task_queue=task_queue,
                ),
            )
            response_data = response.json()

            # Check if this is a synchronous response by looking for wait_for_result
            if wait_for_result:
                return await self._decode_response(WorkflowExecutionSyncResponse.model_validate(response_data))
            else:
                return await self._decode_response(WorkflowExecutionResponse.model_validate(response_data))
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to execute workflow", code=ErrorCode.POST_WORKFLOWS_EXECUTE_ERROR
            ) from exc

    async def terminate_workflow_execution(
        self,
        execution_id: str,
    ) -> None:
        """Execute a workflow.

        Args:
            execution_id: The id of the workflow execution to terminate.

        Returns:
            None
        """
        try:
            response = await self._request(
                "POST",
                f"/executions/{execution_id}/terminate",
                data=TerminateWorkflowRequest(
                    execution_id=execution_id,
                ),
            )
            assert response.status_code == 204
            return
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to terminate workflow execution", code=ErrorCode.POST_EXECUTIONS_TERMINATE_ERROR
            ) from exc

    async def reset_workflow(
        self,
        execution_id: str,
        event_id: int,
        reason: str | None = None,
        exclude_signals: bool = False,
        exclude_updates: bool = False,
    ) -> None:
        """Reset a workflow execution to a specific event ID.

        Args:
            execution_id: The ID of the workflow execution to reset.
            event_id: The event ID to reset to.
            reason: Optional reason for the reset.
            exclude_signals: Whether to exclude signals that happened after the reset point.
            exclude_updates: Whether to exclude updates that happened after the reset point.

        Returns:
            None
        """
        try:
            response = await self._request(
                "POST",
                f"/executions/{execution_id}/reset",
                data=ResetInvocationBody(
                    event_id=event_id,
                    reason=reason,
                    exclude_signals=exclude_signals,
                    exclude_updates=exclude_updates,
                ),
            )
            assert response.status_code == 204
            return
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to reset workflow execution", code=ErrorCode.TEMPORAL_SERVICE_ERROR
            ) from exc

    async def get_workflow_executions(
        self,
        workflow_identifier: str | uuid.UUID | None = None,
        page_size: int = 50,
        next_page_token: str | None = None,
    ) -> WorkflowExecutionListResponse:
        """Get all workflow executions with token-based pagination.

        Args:
            page_size: Number of items per page
            next_page_token: Token for the next page of results

        Returns:
            A list of workflow executions with pagination information.
        """
        params: Dict[str, Any] = {"page_size": page_size}
        if workflow_identifier:
            params["workflow_identifier"] = workflow_identifier
        if next_page_token:
            params["next_page_token"] = next_page_token
        endpoint = "/executions"

        try:
            response = await self._request("GET", endpoint, params=params)
            return WorkflowExecutionListResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to get workflow executions", code=ErrorCode.GET_EXECUTIONS_ERROR
            ) from exc

    async def get_workflow_execution(self, execution_id: str) -> WorkflowExecutionResponse:
        """Get a workflow execution by ID.

        Args:
            execution_id: The ID of the workflow execution.

        Returns:
            The workflow execution.
        """
        try:
            response = await self._request("GET", f"/executions/{execution_id}")
            return await self._decode_response(WorkflowExecutionResponse.model_validate(response.json()))
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to get workflow execution", code=ErrorCode.GET_EXECUTIONS_ERROR
            ) from exc

    async def get_workflow_execution_trace_otel(self, execution_id: str) -> WorkflowExecutionTracOTelResponse:
        """Get the OpenTelemetry trace data for a workflow execution.

        Args:
            execution_id: The ID of the workflow execution.

        Returns:
            The OpenTelemetry trace data.
        """
        try:
            response = await self._request("GET", f"/executions/{execution_id}/trace/otel")
            return WorkflowExecutionTracOTelResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc,
                message="Failed to get workflow execution trace otel",
                code=ErrorCode.GET_EXECUTIONS_TRACE_OTEL_ERROR,
            ) from exc

    async def get_workflow_execution_trace_summary(self, execution_id: str) -> WorkflowExecutionTraceSummaryResponse:
        """Get the trace summary for a workflow execution.

        Args:
            execution_id: The ID of the workflow execution.

        Returns:
            The trace summary.
        """
        try:
            response = await self._request("GET", f"/executions/{execution_id}/trace/summary")
            return WorkflowExecutionTraceSummaryResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc,
                message="Failed to get workflow execution trace summary",
                code=ErrorCode.GET_EXECUTIONS_TRACE_SUMMARY_ERROR,
            ) from exc

    async def get_workflow_execution_trace_events(
        self,
        execution_id: str,
        merge_same_id_events: bool = False,
        include_internal_events: bool = False,
    ) -> WorkflowExecutionTraceEventsResponse:
        """Fetch trace events for a specific workflow execution.

        Args:
            execution_id: The ID of the workflow execution to fetch events for.
            merge_same_id_events: If True, merges events with the same ID, retaining the last one.
                                  Useful for UI progress display to show the latest event status.
            include_internal_events: If True, includes internal events in the response.

        Returns:
            WorkflowExecutionTraceEventsResponse: An object containing the trace events.
        """
        try:
            response = await self._request(
                "GET",
                f"/executions/{execution_id}/trace/events",
                params={
                    "merge_same_id_events": merge_same_id_events,
                    "include_internal_events": include_internal_events,
                },
            )
            return WorkflowExecutionTraceEventsResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc,
                message="Failed to get workflow execution trace events",
                code=ErrorCode.GET_EXECUTIONS_TRACE_EVENTS_ERROR,
            ) from exc

    async def wait_for_workflow_completion(
        self,
        execution_id: str,
        polling_interval: int = 5,
        max_attempts: int | None = None,
    ) -> WorkflowExecutionResponse:
        """Wait for a workflow to complete by polling its status.

        Args:
            execution_id: Execution ID of the workflow
            polling_interval: Seconds between status checks
            max_attempts: Maximum number of polling attempts (None for unlimited)

        Returns:
            WorkflowExecutionResponse with the final execution details

        Raises:
            TimeoutError: If max_attempts is reached and workflow is still running
            RuntimeError: If workflow fails or terminates abnormally
        """
        attempts = 0
        try:
            while True:
                response = await self.get_workflow_execution(execution_id)

                if response.status != WorkflowExecutionStatus.RUNNING:
                    if response.status == WorkflowExecutionStatus.COMPLETED:
                        return response
                    else:
                        raise WorkflowsException(
                            message=f"Workflow failed with status: {response.status}",
                            code=ErrorCode.GET_EXECUTIONS_ERROR,
                        )

                attempts += 1
                if max_attempts is not None and attempts >= max_attempts:
                    raise WorkflowsException(
                        message=f"Workflow is still running after {max_attempts} polling attempts",
                        code=ErrorCode.GET_EXECUTIONS_ERROR,
                    )

                await asyncio.sleep(polling_interval)
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed while waiting for workflow completion", code=ErrorCode.GET_EXECUTIONS_ERROR
            ) from exc

    async def execute_workflow_and_wait(
        self,
        workflow_identifier: str,
        input_data: BaseModel | None,
        task_queue: str | None = None,
        execution_id: str | None = None,
        polling_interval: int = 5,
        max_attempts: int | None = None,
        use_api_sync: bool = False,
        timeout_seconds: float | None = None,
        custom_tracing_attributes: Dict[str, str] | None = None,
    ) -> Any:
        """Execute a workflow and wait for its completion.

        Args:
            workflow_identifier: The workflow name or ID.
            input_data: Input parameters for the workflow
            execution_id: Optional custom execution ID
            polling_interval: Seconds between status checks when polling
            max_attempts: Maximum number of polling attempts when polling (None for unlimited)
            use_api_sync: Whether to use the API's built-in sync execution capability
            timeout_seconds: Maximum time to wait in seconds when using API sync

        Returns:
            The workflow result directly

        Raises:
            TimeoutError: If max_attempts is reached and workflow is still running
            RuntimeError: If workflow fails or terminates abnormally
            httpx.HTTPStatusError: If API request fails (including timeouts)
        """
        try:
            if use_api_sync:
                # Use the API's built-in synchronous execution
                response = await self.execute_workflow(
                    workflow_identifier,
                    input_data=input_data,
                    execution_id=execution_id,
                    wait_for_result=True,
                    timeout_seconds=timeout_seconds,
                    custom_tracing_attributes=custom_tracing_attributes,
                    task_queue=task_queue,
                )
                return response.result
            else:
                # Use polling method
                execution = await self.execute_workflow(
                    workflow_identifier,
                    input_data=input_data,
                    execution_id=execution_id,
                    custom_tracing_attributes=custom_tracing_attributes,
                    task_queue=task_queue,
                )

                # Wait for completion
                final_execution = await self.wait_for_workflow_completion(
                    execution.execution_id, polling_interval, max_attempts
                )

                return final_execution.result
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to execute workflow and wait", code=ErrorCode.POST_WORKFLOWS_EXECUTE_ERROR
            ) from exc

    async def _encode_input_if_needed(
        self,
        execution_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any] | Any | NetworkEncodedInput | None:
        if not self.payload_encoder:
            return input_data
        encoded_input = await self.payload_encoder.encode_network_input(
            input_data,
            context=WorkflowContext(
                namespace=await self.get_scheduler_namespace(),
                execution_id=execution_id,
            ),
        )
        return encoded_input

    async def signal_workflow(
        self,
        execution_id: str,
        signal_name: str,
        input_data: BaseModel | None = None,
    ) -> SignalWorkflowResponse:
        """Send a signal to a running workflow execution."""
        endpoint = f"/executions/{execution_id}/signals"
        try:
            input_data_dict = input_data.model_dump(mode="json") if input_data else {}
            encoded_input = await self._encode_input_if_needed(execution_id, input_data_dict)
            request_body = SignalInvocationBody(name=signal_name, input=encoded_input)
            logger.debug(
                "WorkflowsClient: Sending signal",
                execution_id=execution_id,
                signal_name=signal_name,
            )
            response = await self._request("POST", endpoint, data=request_body)
            return SignalWorkflowResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to signal workflow", code=ErrorCode.POST_EXECUTIONS_SIGNALS_ERROR
            ) from exc

    async def query_workflow(
        self,
        execution_id: str,
        query_name: str,
        input_data: BaseModel | None = None,
    ) -> QueryWorkflowResponse:
        """Query a running workflow execution."""
        endpoint = f"/executions/{execution_id}/queries"
        try:
            input_data_dict = input_data.model_dump(mode="json") if input_data else {}
            encoded_input = await self._encode_input_if_needed(execution_id, input_data_dict)
            request_body = QueryInvocationBody(name=query_name, input=encoded_input)
            logger.debug(
                "WorkflowsClient: Sending query",
                execution_id=execution_id,
                query_name=query_name,
            )
            response = await self._request("POST", endpoint, data=request_body)
            return await self._decode_response(QueryWorkflowResponse.model_validate(response.json()))
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to query workflow", code=ErrorCode.POST_EXECUTIONS_QUERIES_ERROR
            ) from exc

    async def update_workflow(
        self,
        execution_id: str,
        update_name: str,
        input_data: BaseModel | None = None,
    ) -> UpdateWorkflowResponse:
        """Send an update to a running workflow execution.

        Args:
            execution_id (str): The execution ID of the workflow to update.
            update_name (str): The name of the update to send.
            input_data (Dict[str, Any] | None, optional): The input data for the update. Defaults to None.

        Returns:
            UpdateWorkflowResponse: The response from the server.
        """
        endpoint = f"/executions/{execution_id}/updates"
        try:
            input_data_dict = input_data.model_dump(mode="json") if input_data else {}

            encoded_input = await self._encode_input_if_needed(execution_id, input_data_dict)
            request_body = UpdateInvocationBody(name=update_name, input=encoded_input)
            logger.debug("WorkflowsClient: Sending update", execution_id=execution_id, update_name=update_name)
            response = await self._request("POST", endpoint, data=request_body)
            return await self._decode_response(UpdateWorkflowResponse.model_validate(response.json()))
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to update workflow", code=ErrorCode.POST_EXECUTIONS_UPDATES_ERROR
            ) from exc

    async def schedule_workflow(
        self,
        schedule: ScheduleDefinition,
        schedule_id: str | None = None,
        workflow_version_id: uuid.UUID | None = None,
        workflow_identifier: str | None = None,
        workflow_task_queue: str | None = None,
    ) -> WorkflowScheduleResponse:
        """Schedule a workflow execution. Either by name, or version id"""
        try:
            if not workflow_version_id and not workflow_identifier:
                raise WorkflowsException(
                    message="Either workflow_version_id or workflow_identifier must be provided",
                    code=ErrorCode.INVALID_ARGUMENTS_ERROR,
                )
            elif workflow_version_id and workflow_identifier:
                raise WorkflowsException(
                    message="Only one of workflow_version_id or workflow_identifier can be provided",
                    code=ErrorCode.INVALID_ARGUMENTS_ERROR,
                )

            if workflow_identifier and not workflow_task_queue:
                # Fallback on default task queue:
                workflow_task_queue = config.temporal.task_queue

            endpoint = "/schedules"

            schedule.input = await self._encode_input_if_needed(
                SCHEDULE_CORRELATION_ID_PLACEHOLDER,
                schedule.input,
            )

            request_body = WorkflowScheduleRequest(
                schedule=schedule,
                schedule_id=schedule_id,
                workflow_version_id=workflow_version_id,
                workflow_identifier=workflow_identifier,
                workflow_task_queue=workflow_task_queue,
            )

            response = await self._request("POST", endpoint, data=request_body)
            return WorkflowScheduleResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to schedule workflow", code=ErrorCode.POST_SCHEDULES_ERROR
            ) from exc

    async def unschedule_workflow(self, schedule_id: str) -> None:
        """Unschedule a workflow execution."""
        try:
            await self._request("DELETE", f"/schedules/{schedule_id}")
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to unschedule workflow", code=ErrorCode.DELETE_SCHEDULES_ERROR
            ) from exc

    async def get_schedules(self) -> WorkflowScheduleListResponse:
        """Get all workflow schedules."""
        try:
            response = await self._request("GET", "/schedules")
            return WorkflowScheduleListResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to get schedules", code=ErrorCode.GET_SCHEDULES_ERROR
            ) from exc

    async def send_event(self, event: WorkflowEvent) -> WorkflowEventResponse:
        """Send a workflow event to the API.

        Args:
            event: The workflow event to send.

        Returns:
            The response from the server.
        """
        try:
            response = await self._request(
                "POST",
                "/events",
                data=WorkflowEventRequest(event=event),
            )
            return WorkflowEventResponse.model_validate(response.json())
        except Exception as exc:
            raise WorkflowsException.from_api_client_error(
                exc, message="Failed to send workflow event", code=ErrorCode.POST_EVENTS_ERROR
            ) from exc
