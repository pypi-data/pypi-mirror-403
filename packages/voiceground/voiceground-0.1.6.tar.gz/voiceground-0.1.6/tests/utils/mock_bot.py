"""Mock bot for testing Voiceground simulations."""

import uuid

from pipecat.frames.frames import CancelFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.transports.base_transport import BaseTransport

from tests.utils.mock_components import MockLLMService


async def run_mock_bot(
    transport: BaseTransport,
    responses: list[str],
    system_prompt: str = "You are a helpful assistant.",
) -> None:
    """Run a mock bot with predetermined responses.

    Args:
        transport: The transport to use for the bot.
        responses: List of predetermined responses for the bot to give.
        system_prompt: System prompt for the bot's context.
    """
    conversation_id = str(uuid.uuid4())

    # Create LLM with predetermined responses
    llm = MockLLMService(responses=responses)

    # Set up conversation context
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    context = LLMContext(messages)
    context_aggregator = LLMContextAggregatorPair(context)

    # Build text-only pipeline
    pipeline = Pipeline(
        [
            transport.input(),
            context_aggregator.user(),
            llm,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(pipeline, conversation_id=conversation_id)

    # Handle client disconnect
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, *args, **kwargs):
        await task.queue_frame(CancelFrame())

    runner = PipelineRunner()
    await runner.run(task)
