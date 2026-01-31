import asyncio

import structlog
from pydantic import Field

import mistralai_workflows as workflows
import mistralai_workflows.plugins.agents as workflows_agents
import mistralai_workflows.plugins.mistralai as workflows_mistralai

logger = structlog.get_logger(__name__)


class FavoritePokemonInput(workflows_mistralai.ChatInput):
    """Input schema for asking the user's favorite Pokemon."""

    pokemon_name: str = Field(description="The name of your favorite Pokemon")


class LeastFavoritePokemonInput(workflows_mistralai.ChatInput):
    """Input schema for asking the user's least favorite Pokemon."""

    pokemon_name: str = Field(description="The name of your least favorite Pokemon")


@workflows.workflow.define(
    name="pokemon-personality-workflow",
    workflow_display_name="Pokemon Personality",
    workflow_description="Discover your personality based on your Pokemon preferences",
)
class PokemonPersonalityWorkflow(workflows.InteractiveWorkflow):
    @workflows.workflow.entrypoint
    async def run(self) -> workflows_mistralai.ChatAssistantWorkflowOutput:
        async with workflows.task_from(
            state=workflows_mistralai.ChatAssistantWorkingTask(
                title="Pokemon Personality Quiz",
                content="Starting the personality quiz...",
            )
        ) as task:
            await task.update_state(updates={"content": "Waiting for your favorite Pokemon..."})

            # Step 1: Ask for favorite pokemon
            favorite = await self.wait_for_input(FavoritePokemonInput)
            logger.info("Received favorite Pokemon", pokemon=favorite.pokemon_name)

            await task.update_state(
                updates={
                    "content": f"Got it! Your favorite is {favorite.pokemon_name}. "
                    "Now waiting for your least favorite..."
                }
            )

            # Step 2: Ask for least favorite pokemon
            least_favorite = await self.wait_for_input(LeastFavoritePokemonInput)
            logger.info("Received least favorite Pokemon", pokemon=least_favorite.pokemon_name)

            await task.update_state(
                updates={
                    "content": f"Analyzing your personality based on {favorite.pokemon_name} "
                    f"and {least_favorite.pokemon_name}..."
                }
            )

        # Step 3: Generate personality description using an agent
        logger.info("Creating personality analysis agent")
        session = workflows_agents.RemoteSession(stream=True)

        personality_agent = workflows_agents.Agent(
            model="mistral-medium-2508",
            description="Pokemon personality analyst that creates fun personality profiles",
            instructions="""You are a fun and insightful personality analyst who specializes in understanding
people through their Pokemon preferences. When given a favorite and least favorite Pokemon,
you create an engaging personality analysis.

Write a short, engaging personality description (2-3 paragraphs) that:
1. Analyzes what the favorite Pokemon choice says about the person's values and personality
2. Analyzes what the least favorite Pokemon choice reveals about what they avoid or dislike
3. Synthesizes these insights into a cohesive personality profile

Be creative, fun, and positive while still being insightful!""",
            name="pokemon-personality-agent",
        )

        prompt = f"""Analyze this person's personality based on their Pokemon preferences:

Favorite Pokemon: {favorite.pokemon_name}
Least Favorite Pokemon: {least_favorite.pokemon_name}

Please provide your personality analysis."""

        logger.info("Running personality agent", prompt=prompt)
        await workflows_agents.Runner.run(
            agent=personality_agent,
            inputs=prompt,
            session=session,
        )

        return workflows_mistralai.ChatAssistantWorkflowOutput(
            outputs=[workflows_mistralai.TextOutput(text="Come back for more Pokemon based Quiz another time!")]
        )


if __name__ == "__main__":
    asyncio.run(workflows.run_worker([PokemonPersonalityWorkflow]))
