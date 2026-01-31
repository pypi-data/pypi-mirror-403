import asyncio
from typing import List

import pydantic
import structlog

import mistralai_workflows as workflows
from mistralai_workflows.core.config.config import config
from mistralai_workflows.core.logging import setup_logging
from mistralai_workflows.examples.assist.workflow_insurance_claims import InsuranceClaimsWorkflow
from mistralai_workflows.examples.assist.workflow_multi_turn_chat import MultiTurnChatWorkflow
from mistralai_workflows.examples.assist.workflow_pokemon_personality import PokemonPersonalityWorkflow

logger = structlog.getLogger(__name__)


class Params(pydantic.BaseModel):
    query: str


class TextOutput(pydantic.BaseModel):
    type: str = "text"
    text: str


class Result(pydantic.BaseModel):
    outputs: List[TextOutput] = pydantic.Field(description="List of results")


@workflows.activity()
async def assist_activity(query: str) -> Result:
    async with workflows.task("activity.processing", {"query": query}):
        await asyncio.sleep(1)

    return Result(outputs=[TextOutput(text="result1"), TextOutput(text="result2")])


@workflows.workflow.define(
    name="assist-workflow-hello-world",
    workflow_display_name="Hello World assist",
    workflow_description="Example workflow",
)
class Workflow:
    @workflows.workflow.entrypoint
    async def run(self, document_title: str) -> Result:
        results = await assist_activity(document_title)
        return results


if __name__ == "__main__":
    setup_logging(
        log_format=config.common.log_format,
        log_level=config.common.log_level,
        app_version=config.common.app_version,
    )
    asyncio.run(
        workflows.run_worker([Workflow, PokemonPersonalityWorkflow, MultiTurnChatWorkflow, InsuranceClaimsWorkflow])
    )
