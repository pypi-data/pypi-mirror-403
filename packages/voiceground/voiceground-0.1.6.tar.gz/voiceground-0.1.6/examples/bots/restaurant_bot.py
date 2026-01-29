"""Restaurant booking bot - example bot for Voiceground.

This bot can be used standalone or with Voiceground's simulation feature.
It accepts STT, LLM, and TTS services as parameters for flexibility.
"""

import uuid
from typing import TYPE_CHECKING

from loguru import logger
from pipecat.frames.frames import CancelFrame
from pipecat.observers.base_observer import BaseObserver
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.llm_service import LLMService
from pipecat.services.stt_service import STTService
from pipecat.services.tts_service import TTSService
from pipecat.transports.base_transport import BaseTransport

if TYPE_CHECKING:
    pass

# Bot system prompt
SYSTEM_PROMPT = """You are a helpful restaurant booking assistant for "The Golden Fork" restaurant.

You can help customers:
- Make reservations (ask for date, time, party size, name)
- Answer questions about the menu (Italian cuisine)
- Provide restaurant hours (open 11am-10pm daily)

Be friendly, professional, and concise. Confirm reservation details before finalizing."""


async def run_restaurant_bot(
    transport: BaseTransport,
    stt: STTService,
    llm: LLMService,
    tts: TTSService,
    observers: list[BaseObserver] = None,
) -> None:
    """Run the restaurant booking bot.

    This bot works with any Pipecat transport - LocalAudioTransport for
    production, WebsocketTransport for web apps, or VoicegroundBridgeTransport
    for simulation testing.

    Args:
        transport: The Pipecat transport to use (any BaseTransport).
        stt: Speech-to-text service.
        llm: Large language model service.
        tts: Text-to-speech service.
        observers: Optional list of observers to attach to the pipeline.
    """
    if observers is None:
        observers = []
    conversation_id = str(uuid.uuid4())

    # Set up conversation context
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    context = LLMContext(messages)
    context_aggregator = LLMContextAggregatorPair(context)

    # Build pipeline
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    # Create task
    task = PipelineTask(
        pipeline,
        observers=observers,
        conversation_id=conversation_id,
    )

    # Handle client disconnect (important for simulation)
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, *args, **kwargs):
        logger.info("Client disconnected, stopping bot")
        await task.queue_frame(CancelFrame())

    runner = PipelineRunner()
    await runner.run(task)
