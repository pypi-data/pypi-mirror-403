from __future__ import annotations

from typing import Any, Literal, cast

import structlog
from mistralai_workflows.core.config.config import config
from mistralai_workflows.core.rate_limiting.rate_limit import RateLimit
from mistralai_workflows.core.task import Task

import mistralai
from mistralai.utils import eventstreaming
from mistralai_workflows.plugins.mistralai.models import ChatStreamState, ContentChunk, ConversationStreamState

_MISTRAL_LLM_RATE_LIMIT_DEFAULT_KEY = "__MISTRAL_LLM_RATE_LIMIT_DEFAULT_KEY"


def get_mistral_client() -> mistralai.Mistral:
    api_key_secret = config.worker.agent.mistral_client_api_key
    api_key = api_key_secret.get_secret_value() if api_key_secret else None
    return mistralai.Mistral(
        api_key=api_key or None,
        server=config.worker.agent.mistral_client_server,
        server_url=config.worker.agent.mistral_client_server_url,
        url_params=config.worker.agent.mistral_client_url_params,
        timeout_ms=config.worker.agent.mistral_client_timeout_ms,
    )


def _get_agent_llm_rate_limit() -> RateLimit | None:
    llm_rate_limit = config.worker.agent.llm_rate_limit
    if llm_rate_limit is None:
        return None
    if llm_rate_limit.key is None:
        llm_rate_limit.key = _MISTRAL_LLM_RATE_LIMIT_DEFAULT_KEY
    return llm_rate_limit


logger = structlog.get_logger(__name__)


# FIXME : Add cost informations - depends on agent team
async def handle_conversation_stream(
    stream: eventstreaming.EventStreamAsync[mistralai.ConversationEvents],
) -> mistralai.ConversationResponse:
    aggregated_content = ""
    tool_calls: dict[int, mistralai.ToolExecutionEntry] = {}
    function_calls: dict[int, mistralai.FunctionCallEntry] = {}
    handoffs: dict[str, mistralai.AgentHandoffEntry] = {}
    conversation_id: str = ""
    outputs: list[mistralai.Outputs] = []
    async with Task[ConversationStreamState](type="assistant_message", state=ConversationStreamState()) as task:
        async for chunk in stream.generator:
            if isinstance(chunk.data, mistralai.ResponseStartedEvent):
                conversation_id = chunk.data.conversation_id

            elif isinstance(chunk.data, mistralai.ResponseDoneEvent):
                outputs.append(mistralai.MessageOutputEntry(content=aggregated_content, type="message.output"))

            elif isinstance(chunk.data, mistralai.MessageOutputEvent):
                if isinstance(chunk.data.content, str):
                    aggregated_content += chunk.data.content
                    await task.set_state(ConversationStreamState(contentChunks=[ContentChunk(text=aggregated_content)]))

                elif isinstance(chunk.data.content, list):
                    logger.debug(
                        "Streaming delta contained non-text content; skipping for now",
                        content_type=type(chunk.data.content),
                    )
            elif isinstance(chunk.data, mistralai.FunctionCallEvent):
                index = chunk.data.output_index or 0
                existing_function = function_calls.get(index)

                if not existing_function:
                    function_call = mistralai.FunctionCallEntry(
                        tool_call_id=chunk.data.tool_call_id,
                        name=chunk.data.name,
                        arguments="",
                        type="function.call",
                    )
                    function_calls[index] = function_call
                else:
                    if chunk.data.id and chunk.data.id != existing_function.id:
                        existing_function.id = chunk.data.id
                    if chunk.data.name:
                        existing_function.name = chunk.data.name
                    if chunk.data.arguments:
                        previous_args = existing_function.arguments or ""
                        new_args = chunk.data.arguments
                        if isinstance(previous_args, str):
                            existing_function.arguments = previous_args + new_args
                        else:
                            existing_function.arguments = new_args

            elif isinstance(chunk.data, mistralai.ToolExecutionDeltaEvent):
                index = chunk.data.output_index or 0
                existing_tool = tool_calls.get(index)

                if not existing_tool:
                    if isinstance(chunk.data, mistralai.ToolExecutionDeltaEvent):
                        tool_call = mistralai.ToolExecutionEntry(
                            name=chunk.data.name,
                            arguments="",
                            id=chunk.data.id,
                            type="tool.execution",
                        )

                        tool_calls[index] = tool_call

                else:
                    if chunk.data.id and chunk.data.id != existing_tool.id:
                        existing_tool.id = chunk.data.id
                    if chunk.data.name:
                        existing_tool.name = chunk.data.name
                    if chunk.data.arguments:
                        previous_args = existing_tool.arguments
                        new_args = chunk.data.arguments
                        existing_tool.arguments = previous_args + new_args

            elif isinstance(chunk.data, mistralai.ToolExecutionDoneEvent):
                outputs.append(tool_calls[chunk.data.output_index or 0])
            elif isinstance(chunk.data, mistralai.AgentHandoffStartedEvent):
                handoff_id = chunk.data.id
                if handoff_id in handoffs:
                    logger.error(
                        "This handoff is already registered..., this should never happen... Overwriting the handoff."
                    )
                if not handoff_id:
                    logger.error("This handoff has no id ..., overwriting element with empty key.")
                handoffs[handoff_id] = mistralai.AgentHandoffEntry(
                    previous_agent_id=chunk.data.previous_agent_id,
                    previous_agent_name=chunk.data.previous_agent_name,
                    next_agent_id="",
                    next_agent_name="",
                    id=handoff_id,
                    type="agent.handoff",
                )
            elif isinstance(chunk.data, mistralai.AgentHandoffDoneEvent):
                handoff_id = chunk.data.id
                if handoff_id not in handoffs:
                    logger.error("This handoff should already be registered..., this should never happen... Passing...")
                    pass
                if not handoff_id:
                    logger.error("This handoff has no id ..., overwriting element with empty key.")

                handoffs[handoff_id].next_agent_id = chunk.data.next_agent_id
                handoffs[handoff_id].next_agent_name = chunk.data.next_agent_name
                outputs.append(handoffs[handoff_id])

    message_payload: dict[str, object] = {}

    message_payload["outputs"] = outputs + list(function_calls.values())
    message_payload["conversation_id"] = conversation_id
    message_payload["usage"] = mistralai.ConversationUsageInfo()  # FIXME : fill that

    return mistralai.ConversationResponse.model_validate(message_payload)


async def handle_chat_stream(
    stream: eventstreaming.EventStreamAsync[mistralai.CompletionEvent],
) -> mistralai.AssistantMessage:
    aggregated_content = ""
    role: Literal["assistant"] | None = None
    tool_calls: dict[int, mistralai.ToolCall] = {}

    async with Task[ChatStreamState](type="assistant_message", state=ChatStreamState()) as task:
        async for chunk in stream.generator:
            if not chunk.data.choices:
                continue

            choice = chunk.data.choices[0]
            delta = choice.delta

            if isinstance(delta.role, str) and delta.role == "assistant":
                role = cast(Literal["assistant"], "assistant")

            delta_content = delta.content
            if isinstance(delta_content, str):
                aggregated_content += delta_content
                await task.set_state(ChatStreamState(contentChunks=[ContentChunk(text=aggregated_content)]))
            elif isinstance(delta_content, list):
                logger.debug(
                    "Streaming delta contained non-text content; skipping for now",
                    content_type=type(delta_content),
                )

            if delta.tool_calls:
                for partial in delta.tool_calls:
                    index = partial.index if partial.index is not None else 0
                    existing = tool_calls.get(index)

                    function_name = ""
                    function_arguments: str | dict[str, Any] = ""
                    if partial.function:
                        if partial.function.name:
                            function_name = partial.function.name
                        if partial.function.arguments:
                            function_arguments = partial.function.arguments

                    if existing is None:
                        tool_call = mistralai.ToolCall(
                            id=partial.id,
                            type=partial.type,
                            index=partial.index,
                            function=mistralai.FunctionCall(
                                name=function_name,
                                arguments=function_arguments,
                            )
                            if partial.function
                            else mistralai.FunctionCall(name=function_name, arguments=""),
                        )
                        tool_calls[index] = tool_call
                    else:
                        if partial.id and partial.id != existing.id:
                            existing.id = partial.id
                        if partial.type:
                            existing.type = partial.type
                        if partial.function:
                            if partial.function.name:
                                existing.function.name = partial.function.name
                            if partial.function.arguments:
                                previous_args = existing.function.arguments or ""
                                new_args = partial.function.arguments
                                if isinstance(previous_args, str) and isinstance(new_args, str):
                                    existing.function.arguments = previous_args + new_args
                                else:
                                    existing.function.arguments = new_args

    message_payload: dict[str, object] = {}
    if role is not None:
        message_payload["role"] = role
    if aggregated_content:
        message_payload["content"] = aggregated_content
    if tool_calls:
        message_payload["tool_calls"] = list(tool_calls.values())

    return mistralai.AssistantMessage.model_validate(message_payload)
