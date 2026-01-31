import asyncio
import os
from itertools import count

import mistralai

# Import actual types for type checking
from mistralai import ChatCompletionRequest, Messages, Mistral, UserMessage
from pydantic import BaseModel, Field

import mistralai_workflows as workflows
import mistralai_workflows.plugins.mistralai as workflows_mistralai
from mistralai_workflows.plugins.mistralai.activities import mistralai_chat_stream


class WorkflowParams(BaseModel):
    model: str = "mistral-medium-2508"
    message: str


# Type aliases for better type checking
# UserMessage = UserMessage
# AssistantMessage = AssistantMessage
# Messages = Messages
# Mistral = Mistral
# ChatCompletionRequest = ChatCompletionRequest


class ConversationInput(workflows_mistralai.ChatInput):
    message: str = Field(description="Your next message")


@workflows.workflow.define(
    name="multi_turn_chat_workflow",
    workflow_description="Multi-turn chat workflow using Mistral AI",
)
class MultiTurnChatWorkflow(workflows.InteractiveWorkflow):
    @workflows.workflow.entrypoint
    async def run(self, params: WorkflowParams) -> None:
        initial_message = UserMessage(content=params.message)

        messages: list[Messages] = []
        async with workflows.task_from(
            state=workflows_mistralai.ChatAssistantWorkingTask(title="Conversation", content="")
        ) as task:
            await task.update_state(updates={"title": f"Generating assistant response ({1} steps)", "content": ""})
            messages.append(mistralai.UserMessage.model_validate(initial_message.model_dump()))
            assistant_message = await mistralai_chat_stream(
                ChatCompletionRequest(model=params.model, messages=messages)
            )
            messages.append(assistant_message)

            for i in count():
                await task.update_state(updates={"title": f"Waiting for user input ({i + 2} steps)", "content": ""})
                user_message = await self.wait_for_input(ConversationInput)

                await task.update_state(
                    updates={"title": f"Generating assistant response ({i + 2} steps)", "content": ""}
                )
                messages.append(mistralai.UserMessage(content=user_message.message))
                assistant_message = await mistralai_chat_stream(
                    ChatCompletionRequest(model=params.model, messages=messages)
                )
                messages.append(assistant_message)


def get_mistral_client() -> Mistral:
    return Mistral(api_key=os.getenv("PROD_MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY"))


if __name__ == "__main__":
    asyncio.run(workflows.run_worker([MultiTurnChatWorkflow]))
