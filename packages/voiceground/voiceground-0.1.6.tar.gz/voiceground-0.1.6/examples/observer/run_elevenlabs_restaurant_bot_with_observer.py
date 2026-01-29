#!/usr/bin/env python3
"""Run the restaurant bot with ElevenLabs services (STT, TTS) and OpenAI (LLM).

This example demonstrates the restaurant booking bot using ElevenLabs for
speech services and OpenAI for the language model.

Requirements:
    pip install "pipecat-ai[openai,elevenlabs,local]"

    On macOS, also install portaudio (required for pyaudio):
    brew install portaudio

Environment variables:
    OPENAI_API_KEY: Your OpenAI API key
    ELEVENLABS_API_KEY: Your ElevenLabs API key
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import aiohttp
from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.services.elevenlabs.stt import ElevenLabsSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

from examples.bots.restaurant_bot import run_restaurant_bot
from voiceground import HTMLReporter, MetricsReporter, VoicegroundObserver

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")


def verify_keys(**keys: str | None) -> None:
    """Verify that all required API keys are present.

    Args:
        **keys: Key-value pairs where key is the environment variable name
                and value is the key value from os.getenv().

    Exits with code 1 if any key is missing, printing an error message.
    """
    missing = [name for name, value in keys.items() if not value]
    if missing:
        for name in missing:
            print(f"❌ {name} environment variable is required")
        sys.exit(1)


async def main():
    """Run the restaurant bot with ElevenLabs and OpenAI services."""
    # Validate API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = "21m00Tcm4TlvDq8ikWAM"

    verify_keys(
        OPENAI_API_KEY=openai_key,
        ELEVENLABS_API_KEY=elevenlabs_key,
    )

    # Configure local audio transport
    transport = LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        )
    )

    async with aiohttp.ClientSession() as session:
        # Initialize services
        stt = ElevenLabsSTTService(
            api_key=elevenlabs_key,
            aiohttp_session=session,
        )
        llm = OpenAILLMService(api_key=openai_key, model="gpt-4o-mini")
        tts = ElevenLabsTTSService(
            api_key=elevenlabs_key,
            aiohttp_session=session,
            voice_id=voice_id,
        )

        # Create Voiceground observer with reporters
        html_reporter = HTMLReporter(output_dir="reports", auto_open=True)
        metrics_reporter = MetricsReporter()
        observer = VoicegroundObserver(reporters=[html_reporter, metrics_reporter])

        await run_restaurant_bot(
            transport=transport,
            stt=stt,
            llm=llm,
            tts=tts,
            observers=[observer],
        )


if __name__ == "__main__":
    asyncio.run(main())
