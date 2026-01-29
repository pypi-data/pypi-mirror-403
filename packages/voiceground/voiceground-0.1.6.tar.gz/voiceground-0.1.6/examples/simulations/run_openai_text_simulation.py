#!/usr/bin/env python3
"""Run a text-only simulation against the restaurant booking bot.

This example shows how to use Voiceground's text-only simulation feature
to test an LLM bot without voice synthesis. Both the simulator and the bot
communicate through text frames, skipping STT/TTS processing.

Requirements:
    pip install "pipecat-ai[openai]"

Environment variables:
    OPENAI_API_KEY: Your OpenAI API key
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from loguru import logger
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.services.openai.tts import OpenAITTSService

from examples.bots.restaurant_bot import run_restaurant_bot
from voiceground import HTMLReporter, SummaryReporter, VoicegroundObserver
from voiceground.evaluations import (
    BooleanEvaluationDefinition,
    CategoryEvaluationDefinition,
    EvaluationType,
    OpenAIEvaluator,
    RatingEvaluationDefinition,
)
from voiceground.simulation import VoicegroundSimulation, VoicegroundSimulatorConfig

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
    # Validate API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    verify_keys(OPENAI_API_KEY=openai_key)

    # Create reporters
    html_reporter = HTMLReporter(output_dir="reports", auto_open=True)
    summary_reporter = SummaryReporter()

    # Create evaluator
    evaluator = OpenAIEvaluator(api_key=openai_key, model="gpt-4o-mini")

    # Define evaluations
    evaluations = [
        BooleanEvaluationDefinition(
            name="goal_achievement",
            criteria="Did the bot successfully help the user complete their goal?",
            evaluator=evaluator,
        ),
        CategoryEvaluationDefinition(
            name="intent_classification",
            criteria="What was the user's intent?",
            categories=["reserve a table", "cancel reservation", "check reservation"],
            evaluator=evaluator,
        ),
        RatingEvaluationDefinition(
            name="bot_politeness",
            criteria="Rate how polite the bot was, where 1 is rude and 5 is very polite",
            min_rating=1,
            max_rating=5,
            evaluator=evaluator,
        ),
    ]

    # Observer with both reporters and evaluations
    observer = VoicegroundObserver(
        reporters=[html_reporter, summary_reporter],
        evaluations=evaluations,
        default_evaluator=evaluator,
    )

    # Configure the simulator (the "fake user")
    simulator_config = VoicegroundSimulatorConfig(
        llm=OpenAILLMService(api_key=openai_key, model="gpt-4o-mini"),
        scenario="You are a customer calling a restaurant to make a reservation for 2 people tomorrow at 7pm under the name Smith",
        termination_criteria="Reservation is confirmed by the resturant.",
        initiate_conversation=True,
        max_turns=10,
        timeout_seconds=120,
        observers=[observer],  # Observers are automatically attached to bot pipeline
        use_voice=False,
    )

    # Run simulation
    async with VoicegroundSimulation(simulator_config) as simulation:
        # Create LLM service for the bot (text-only mode)
        bot_llm = OpenAILLMService(api_key=openai_key, model="gpt-4o-mini")

        # For text-only simulation, run the bot without STT/TTS
        await run_restaurant_bot(
            transport=simulation.transport,
            stt=OpenAISTTService(api_key=openai_key),
            llm=bot_llm,
            tts=OpenAITTSService(api_key=openai_key, voice="alloy"),
        )

    # Display results from SummaryReporter
    logger.info("-" * 50)
    logger.info("Simulation Summary:")
    logger.info(f"  Duration: {summary_reporter.duration_seconds:.2f}s")
    logger.info(f"  Transcript ({len(summary_reporter.transcript_collector.entries)} messages):")
    for entry in summary_reporter.transcript_collector.entries:
        logger.info(f"    [{entry.role.upper()}]: {entry.text}")

    logger.info(f"\n  Evaluations ({len(summary_reporter.evaluations)}):")
    for eval_result in summary_reporter.evaluations:
        if eval_result.type == EvaluationType.BOOLEAN:
            status = "✓ PASSED" if eval_result.passed else "✗ FAILED"
            logger.info(f"    {eval_result.name}: {status}")
        elif eval_result.type == EvaluationType.CATEGORY:
            logger.info(f"    {eval_result.name}: {eval_result.category}")
        elif eval_result.type == EvaluationType.RATING:
            logger.info(f"    {eval_result.name}: {eval_result.rating}/5")
        logger.info(f"      Reasoning: {eval_result.reasoning}")


if __name__ == "__main__":
    asyncio.run(main())
