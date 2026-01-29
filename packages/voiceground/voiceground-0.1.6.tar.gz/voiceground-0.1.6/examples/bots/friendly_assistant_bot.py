"""Friendly assistant bot - example bot for Voiceground.

A simple conversational assistant that accepts STT, LLM, and TTS services
as parameters for flexibility.
"""

import uuid
from typing import TYPE_CHECKING

from loguru import logger
from pipecat.frames.frames import CancelFrame
from pipecat.observers.base_observer import BaseObserver
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.llm_service import LLMService
from pipecat.services.stt_service import STTService
from pipecat.services.tts_service import TTSService
from pipecat.transports.base_transport import BaseTransport

if TYPE_CHECKING:
    pass

# Bot system prompt
SYSTEM_PROMPT = """You are a helpful and friendly AI assistant.
Keep your responses concise and conversational.
You are having a voice conversation, so be natural and engaging."""


async def run_friendly_assistant_bot(
    transport: BaseTransport,
    stt: STTService,
    llm: LLMService,
    tts: TTSService,
    observers: list[BaseObserver] = None,
    enable_metrics: bool = True,
) -> None:
    """Run the friendly assistant bot.

    This bot works with any Pipecat transport - LocalAudioTransport for
    production, WebsocketTransport for web apps, or VoicegroundBridgeTransport
    for simulation testing.

    Args:
        transport: The Pipecat transport to use (any BaseTransport).
        stt: Speech-to-text service.
        llm: Large language model service.
        tts: Text-to-speech service.
        observers: List of observers to attach to the pipeline.
        enable_metrics: Whether to enable pipeline metrics (default: True).
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
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=enable_metrics,
            enable_usage_metrics=enable_metrics,
        ),
        observers=observers,
        conversation_id=conversation_id,
    )

    # Handle client disconnect (important for simulation)
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, *args, **kwargs):
        logger.info("Client disconnected, stopping bot")
        await task.queue_frame(CancelFrame())

    runner = PipelineRunner(handle_sigint=True)
    await runner.run(task)
