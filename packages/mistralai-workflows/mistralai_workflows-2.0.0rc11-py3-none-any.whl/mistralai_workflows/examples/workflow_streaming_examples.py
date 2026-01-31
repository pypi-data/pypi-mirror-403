import asyncio
from typing import AsyncGenerator, List

import structlog
from pydantic import BaseModel, Field
from tqdm import tqdm

import mistralai_workflows as workflows
from mistralai_workflows.core.task import Task

logger = structlog.get_logger()

attempt_counter = 0


class StreamingParams(BaseModel):
    text: str = Field(description="Text to process")
    model: str = Field(description="Model to use", default="test-model")
    items: List[str] = Field(description="List of items to process", default_factory=list)


class StreamingResult(BaseModel):
    processed_text: str = Field(description="Processed text result")
    token_count: int = Field(description="Number of tokens processed")
    items_processed: int = Field(description="Number of items processed", default=0)


class TokenStreamState(BaseModel):
    """State for tracking token streaming progress."""

    tokens: List[str] = Field(default_factory=list)
    current_token: str = ""


async def simulate_llm_token_generator(text: str) -> AsyncGenerator[str, None]:
    """Simulate an LLM token generator"""
    words = text.split()
    for word in words:
        await asyncio.sleep(0.05)  # Simulate streaming delay
        yield word


@workflows.activity()
async def streaming_tokens_activity(params: StreamingParams) -> StreamingResult:
    """
    Example of streaming tokens from a generator using Task API.

    This pattern uses Task to emit lifecycle events and stream progress updates.
    """
    initial_state = TokenStreamState()

    async with Task[TokenStreamState](type="token-stream", state=initial_state) as task:
        state = task.state
        assert state is not None
        async for token in simulate_llm_token_generator(params.text):
            await task.update_state({"tokens": state.tokens + [token], "current_token": token})
            state = task.state
            assert state is not None

    final_state = task.state
    assert final_state is not None
    processed_text = " ".join(final_state.tokens)
    return StreamingResult(processed_text=processed_text, token_count=len(final_state.tokens))


class ProgressState(BaseModel):
    """State for tracking processing progress."""

    processed_words: List[str] = Field(default_factory=list)
    progress_idx: int = 0
    progress_total: int = 0


@workflows.activity(display_name="Processing text with explicit control")
async def streaming_tokens_with_progress_activity(params: StreamingParams) -> StreamingResult:
    """
    Example of explicit progress tracking with Task API.

    This pattern gives you full control over state updates and progress tracking.
    """
    words = params.text.split()
    initial_state = ProgressState(progress_total=len(words))

    async with Task[ProgressState](type="progress-stream", state=initial_state) as task:
        state = task.state
        assert state is not None
        for i, word in tqdm(enumerate(words), total=len(words)):
            await task.update_state(
                {
                    "processed_words": state.processed_words + [word],
                    "progress_idx": i + 1,
                }
            )
            state = task.state
            assert state is not None
            await asyncio.sleep(0.1)

    final_state = task.state
    assert final_state is not None
    return StreamingResult(processed_text=" ".join(final_state.processed_words), token_count=len(words))


@workflows.activity(retry_policy_max_attempts=3, retry_policy_backoff_coefficient=1)
async def streaming_with_retry_activity(params: StreamingParams) -> StreamingResult:
    """Activity that fails on first attempt then succeeds."""
    global attempt_counter
    attempt_counter += 1

    tokens = []

    for i, token in enumerate(params.text):
        tokens.append(token)

        if i == len(params.text) - 1:
            if attempt_counter == 1:
                logger.info("First attempt - will fail")
                raise ValueError("Simulated failure on first attempt")
            elif attempt_counter == 2:
                logger.info("Second attempt - will succeed")
                raise ValueError("Simulated failure on second attempt")

    logger.info(f"Attempt {attempt_counter} - will succeed")
    attempt_counter = 0  # reset for next run

    return StreamingResult(processed_text=" ".join(tokens), token_count=len(tokens))


@workflows.workflow.define(
    name="streaming-tokens-example", workflow_description="Example workflow for streaming tokens"
)
class StreamingTokensWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, params: StreamingParams) -> StreamingResult:
        return await streaming_tokens_activity(params)


@workflows.workflow.define(
    name="streaming-tokens-with-progress-example",
    workflow_description="Example workflow using streaming tokens with progress",
)
class StreamingTokensWithProgressWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, params: StreamingParams) -> StreamingResult:
        return await streaming_tokens_with_progress_activity(params)


@workflows.workflow.define(
    name="streaming-with-retry-example",
    workflow_description="Example workflow using streaming with retry",
)
class StreamingWithRetryWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, params: StreamingParams) -> StreamingResult:
        return await streaming_with_retry_activity(params)
