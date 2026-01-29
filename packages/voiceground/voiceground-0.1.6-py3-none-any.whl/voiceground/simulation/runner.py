"""Simulation runner - orchestrates the simulator pipeline."""

import asyncio
from typing import Any

from loguru import logger
from openai.types.chat import ChatCompletionMessageParam
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame
from pipecat.observers.turn_tracking_observer import TurnTrackingObserver
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.llm_service import FunctionCallParams

from voiceground.observer import VoicegroundObserver
from voiceground.simulation.bridge import (
    VoicegroundBridgeTransport,
    VoicegroundBridgeTransportParams,
)
from voiceground.simulation.config import VoicegroundSimulatorConfig


class VoicegroundSimulation:
    """A simulation environment for testing Pipecat bots.

    Use as an async context manager to run a simulation. The simulation provides a transport
    that is a drop-in replacement for LocalAudioTransport or WebsocketTransport.

    Example:
        async with VoicegroundSimulation(config) as simulation:
            # Use simulation.transport just like LocalAudioTransport
            pipeline = Pipeline([
                simulation.transport.input(),   # Standard transport.input()
                stt, llm, tts,
                simulation.transport.output(),  # Standard transport.output()
            ])

            # Run your bot normally
            task = PipelineTask(pipeline, observers=[...])
            runner = PipelineRunner()
            await runner.run(task)
    """

    def __init__(self, config: VoicegroundSimulatorConfig):
        """Initialize the simulation.

        Args:
            config: Configuration for the simulated user.
        """
        self._config = config

        # Create transport params based on voice mode
        # All observers go to the bot pipeline
        if config.use_voice:
            # Voice mode: enable audio and VAD
            vad_params = VADParams(stop_secs=2.5)
            bot_params = VoicegroundBridgeTransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(params=vad_params),
                observers=config.observers,
            )
            sim_params = VoicegroundBridgeTransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(params=vad_params),
            )
        else:
            # Text-only mode: disable audio
            bot_params = VoicegroundBridgeTransportParams(
                audio_in_enabled=False,
                audio_out_enabled=False,
                vad_analyzer=None,
                observers=config.observers,
            )
            sim_params = VoicegroundBridgeTransportParams(
                audio_in_enabled=False,
                audio_out_enabled=False,
                vad_analyzer=None,
            )

        # Bot transport - this is what the user's bot will use
        self._bot_transport = VoicegroundBridgeTransport(params=bot_params)

        # Simulator transport - paired with bot transport for audio routing
        self._simulator_transport = self._bot_transport.create_paired_transport(params=sim_params)

        # Simulation state
        self._simulator_task: PipelineTask | None = None

    @property
    def transport(self) -> VoicegroundBridgeTransport:
        """Get the transport to use in your bot pipeline.

        This is a drop-in replacement for LocalAudioTransport or any other
        Pipecat transport. Use it exactly as you would use LocalAudioTransport:

            pipeline = Pipeline([
                simulation.transport.input(),   # Receives simulated user audio
                stt, llm, tts,
                simulation.transport.output(),  # Sends bot audio to simulator
            ])
        """
        return self._bot_transport

    async def __aenter__(self) -> "VoicegroundSimulation":
        """Start the simulation."""
        self._run_simulation()
        return self

    def _run_simulation(self) -> None:
        """Run the simulation - create components and start the simulator pipeline."""
        # Build system prompt with scenario and optional termination criteria
        messages: ChatCompletionMessageParam = {
            "role": "system",
            "content": self._config.system_prompt,
        }

        # Setup LLM context with optional end_simulation tool
        if self._config.termination_criteria:
            # Add end_simulation tool for termination criteria
            async def end_simulation_handler(params: FunctionCallParams):
                logger.info("Simulator called end_simulation tool, stopping simulation")
                await params.result_callback({"status": "simulation_ended"})
                if self._simulator_task:
                    await self._simulator_task.cancel()

            tool_description = f"End the simulation. {self._config.termination_criteria}"
            end_simulation_tool = FunctionSchema(
                name="end_simulation",
                description=tool_description,
                properties={},
                required=[],
            )
            tools = ToolsSchema(standard_tools=[end_simulation_tool])
            context = LLMContext(messages=[messages], tools=tools)
            self._config.llm.register_function("end_simulation", end_simulation_handler)
        else:
            context = LLMContext(messages=[messages])

        context_aggregator = LLMContextAggregatorPair(context)

        # Build simulator pipeline based on voice mode
        if self._config.use_voice:
            # Voice mode: include STT and TTS
            assert self._config.stt is not None, "STT service required for voice mode"
            assert self._config.tts is not None, "TTS service required for voice mode"
            simulator_pipeline = Pipeline(
                [
                    self._simulator_transport.input(),
                    self._config.stt,
                    context_aggregator.user(),
                    self._config.llm,
                    self._config.tts,
                    self._simulator_transport.output(),
                    context_aggregator.assistant(),
                ]
            )
        else:
            # Text-only mode: skip STT and TTS
            simulator_pipeline = Pipeline(
                [
                    self._simulator_transport.input(),
                    context_aggregator.user(),
                    self._config.llm,
                    self._simulator_transport.output(),
                    context_aggregator.assistant(),
                ]
            )

        # Setup turn tracking for max turns
        turn_observer = TurnTrackingObserver()

        # Create simulator task - only turn observer on simulator side
        self._simulator_task = PipelineTask(
            simulator_pipeline,
            params=PipelineParams(allow_interruptions=True),
            observers=[turn_observer],
        )

        # Handle bot connection - trigger simulator to start if configured
        @self._simulator_transport.event_handler("on_client_connected")
        async def on_bot_connected(transport):
            if self._config.initiate_conversation and self._simulator_task:
                logger.debug("Bot connected, triggering simulator to start conversation")
                await self._simulator_task.queue_frame(LLMRunFrame())

        @turn_observer.event_handler("on_turn_ended")
        async def on_turn_ended(observer, turn_count, duration, was_interrupted):
            logger.debug(
                f"Turn {turn_count} ended (duration={duration:.2f}s, interrupted={was_interrupted})"
            )
            if turn_count >= self._config.max_turns:
                logger.info(f"Turn limit ({self._config.max_turns}) reached, stopping simulation")
                if self._simulator_task:
                    await self._simulator_task.cancel()

        # Run the simulator pipeline with timeout as a background task
        async def run_with_timeout():
            if not self._simulator_task:
                logger.error("Simulator task not initialized")
                return

            try:
                runner = PipelineRunner(handle_sigint=False)
                await asyncio.wait_for(
                    runner.run(self._simulator_task), timeout=self._config.timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.info(
                    f"Timeout ({self._config.timeout_seconds}s) reached, stopping simulation"
                )
                if self._simulator_task:
                    await self._simulator_task.cancel()
            except Exception as e:
                logger.error(f"Simulation error: {e}", exc_info=True)
                if self._simulator_task:
                    await self._simulator_task.cancel()

        asyncio.create_task(run_with_timeout())

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,  # traceback object type varies by Python version
    ) -> None:
        """Stop the simulation and cleanup."""
        # Stop the simulator if still running
        if self._simulator_task:
            await self._simulator_task.cancel()

        # Close transport
        try:
            await asyncio.wait_for(self._bot_transport.close(), timeout=1.0)
        except asyncio.TimeoutError:
            logger.warning("Bot transport close timed out")

        # Explicitly call end() on all observers to ensure evaluations complete
        for observer in self._config.observers:
            if isinstance(observer, VoicegroundObserver):
                try:
                    await asyncio.wait_for(observer.end(), timeout=60.0)
                except asyncio.TimeoutError:
                    logger.warning("Observer.end() timed out after 60 seconds")
                except Exception as e:
                    logger.error(f"Observer.end() failed: {e}", exc_info=True)
