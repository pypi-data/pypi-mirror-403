"""VoicegroundBridgeTransport - Drop-in transport replacement for simulation.

This module provides a bridge transport that connects two Pipecat pipelines,
enabling closed-loop simulation. It extends Pipecat's base transport classes
to ensure full compatibility with VAD, turn analysis, and interruption handling.
"""

import asyncio
from typing import Optional

from loguru import logger
from pipecat.frames.frames import (
    CancelFrame,
    CancelTaskFrame,
    EndFrame,
    Frame,
    InputAudioRawFrame,
    LLMConfigureOutputFrame,
    LLMFullResponseEndFrame,
    LLMTextFrame,
    OutputAudioRawFrame,
    StartFrame,
    TranscriptionFrame,
)
from pipecat.observers.base_observer import BaseObserver
from pipecat.pipeline.task_observer import TaskObserver
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor, FrameProcessorSetup
from pipecat.transports.base_input import BaseInputTransport
from pipecat.transports.base_output import BaseOutputTransport
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pydantic import ConfigDict


class VoicegroundBridgeTransportParams(TransportParams):
    """Configuration parameters for bridge transport.

    Extends TransportParams with bridge-specific settings.

    Args:
        observers: Optional list of observers to automatically attach to the pipeline
            when it connects.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    observers: list[BaseObserver] | None = None


class VoicegroundBridgeInputTransport(BaseInputTransport):
    """Input transport that receives audio from a bridge queue.

    This extends BaseInputTransport to leverage Pipecat's built-in VAD
    processing, turn analysis, and interruption handling. Audio frames
    received from the paired output transport are pushed to the standard
    audio processing pipeline.
    """

    _params: VoicegroundBridgeTransportParams

    # Timeouts for graceful shutdown stages
    DISCONNECT_TIMEOUT_SECONDS = 5.0  # Wait for bot to handle on_client_disconnected
    CANCEL_TIMEOUT_SECONDS = 5.0  # Wait for CancelTaskFrame to take effect

    # Audio settings for silence generation
    SAMPLE_RATE = 16000
    NUM_CHANNELS = 1
    SILENCE_DURATION_MS = 20  # Duration of silence frames in milliseconds

    def __init__(
        self,
        transport: "VoicegroundBridgeTransport",
        params: VoicegroundBridgeTransportParams,
        audio_queue: "asyncio.Queue[InputAudioRawFrame | None]",
        text_queue: "asyncio.Queue[TranscriptionFrame | None]",
        **kwargs,
    ):
        """Initialize the bridge input transport.

        Args:
            transport: The parent bridge transport.
            params: Transport configuration parameters.
            audio_queue: Queue to receive audio frames from.
            text_queue: Queue to receive text frames from (for text-only mode).
        """
        super().__init__(params, **kwargs)
        self._transport = transport
        self._bridge_audio_queue = audio_queue
        self._bridge_text_queue = text_queue
        self._audio_read_task: asyncio.Task | None = None
        self._text_read_task: asyncio.Task | None = None
        self._disconnected = False
        self._force_stop_task: asyncio.Task | None = None

    async def setup(self, setup: "FrameProcessorSetup"):
        await super().setup(setup)
        # Attach observers to pipeline
        if self._observer and self._transport._observers:
            if isinstance(self._observer, TaskObserver):
                for observer in self._transport._observers:
                    logger.debug(f"Attaching observer {type(observer).__name__} to pipeline")
                    self._observer.add_observer(observer)

    async def start(self, frame: StartFrame):
        """Start the input transport and begin reading from the bridge queue."""
        await super().start(frame)

        await self._transport._call_event_handler("on_client_connected")

        # Configure text-only mode if audio is disabled
        if not self._params.audio_in_enabled:
            # Send configuration frame to skip TTS in text-only mode
            await self.push_frame(LLMConfigureOutputFrame(skip_tts=True))

        # Start appropriate reading task based on audio enabled
        if self._params.audio_in_enabled and not self._audio_read_task:
            self._audio_read_task = self.create_task(self._read_audio_from_bridge())
        elif not self._params.audio_in_enabled and not self._text_read_task:
            self._text_read_task = self.create_task(self._read_text_from_bridge())

        await self.set_transport_ready(frame)

    async def stop(self, frame: EndFrame):
        """Stop the input transport."""
        self._disconnected = True
        await self._cleanup_tasks()
        await super().stop(frame)

    async def cancel(self, frame: CancelFrame):
        """Cancel the input transport."""
        self._disconnected = True
        await self._cleanup_tasks()
        await super().cancel(frame)

    async def _cleanup_tasks(self):
        if self._audio_read_task:
            await self.cancel_task(self._audio_read_task)
            self._audio_read_task = None
        if self._text_read_task:
            await self.cancel_task(self._text_read_task)
            self._text_read_task = None
        if self._force_stop_task:
            self._force_stop_task.cancel()
            try:
                await self._force_stop_task
            except asyncio.CancelledError:
                pass
            self._force_stop_task = None

    def _create_silence_frame(self) -> InputAudioRawFrame:
        """Create a silence audio frame to keep VAD happy during idle periods."""
        num_samples = int(self.SAMPLE_RATE * self.SILENCE_DURATION_MS / 1000)
        silence = bytes(num_samples * self.NUM_CHANNELS * 2)  # 16-bit audio = 2 bytes per sample
        return InputAudioRawFrame(
            audio=silence,
            sample_rate=self.SAMPLE_RATE,
            num_channels=self.NUM_CHANNELS,
        )

    async def _read_audio_from_bridge(self):
        """Read audio from bridge queue and push to VAD processing."""
        while True:
            try:
                try:
                    audio_frame = await asyncio.wait_for(
                        self._bridge_audio_queue.get(),
                        timeout=0.02,  # 20ms for smooth audio
                    )
                except asyncio.TimeoutError:
                    # Send silence to keep VAD happy during idle periods
                    await self.push_audio_frame(self._create_silence_frame())
                    continue

                if audio_frame is None:
                    logger.debug(f"{self} received end of stream signal")
                    await self._transport._call_event_handler("on_client_disconnected")
                    self._force_stop_task = asyncio.create_task(self._force_stop_after_timeout())
                    break

                await self.push_audio_frame(audio_frame)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{self} error reading from bridge: {e}")

    async def _read_text_from_bridge(self):
        """Read text from bridge queue and push to pipeline (text-only mode)."""
        while True:
            try:
                text_frame = await self._bridge_text_queue.get()

                if text_frame is None:
                    logger.debug(f"{self} received end of stream signal (text mode)")
                    await self._transport._call_event_handler("on_client_disconnected")
                    self._force_stop_task = asyncio.create_task(self._force_stop_after_timeout())
                    break

                await self.push_frame(text_frame)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{self} error reading text from bridge: {e}")

    async def _force_stop_after_timeout(self):
        """Force stop the pipeline if bot doesn't respond to disconnect.

        Uses a 3-stage graceful shutdown:
        1. Wait for bot to handle on_client_disconnected
        2. Send CancelTaskFrame upstream
        3. Push CancelFrame to force termination
        """
        try:
            await asyncio.sleep(self.DISCONNECT_TIMEOUT_SECONDS)
            if self._disconnected:
                return

            logger.warning(f"{self} bot didn't stop, sending CancelTaskFrame")
            await self.push_frame(CancelTaskFrame(), direction=FrameDirection.UPSTREAM)

            await asyncio.sleep(self.CANCEL_TIMEOUT_SECONDS)
            if self._disconnected:
                return

            logger.warning(f"{self} forcing immediate termination")
            await self.push_frame(CancelFrame(), direction=FrameDirection.DOWNSTREAM)

        except asyncio.CancelledError:
            pass


class VoicegroundBridgeOutputTransport(BaseOutputTransport):
    """Output transport that sends audio or text to a bridge queue."""

    _params: VoicegroundBridgeTransportParams

    def __init__(
        self,
        params: VoicegroundBridgeTransportParams,
        audio_queue: "asyncio.Queue[InputAudioRawFrame | None]",
        text_queue: "asyncio.Queue[TranscriptionFrame | None]",
        **kwargs,
    ):
        super().__init__(params, **kwargs)
        self._bridge_audio_queue = audio_queue
        self._bridge_text_queue = text_queue
        self._text_buffer: list[str] = []  # Buffer for accumulating LLM text in text-only mode

    async def start(self, frame: StartFrame):
        """Start the output transport."""
        await super().start(frame)
        await self.set_transport_ready(frame)

    async def stop(self, frame: EndFrame):
        """Stop the output transport and signal end of stream."""
        if self._params.audio_out_enabled:
            await self._bridge_audio_queue.put(None)
        else:
            await self._bridge_text_queue.put(None)
        await super().stop(frame)

    async def cancel(self, frame: CancelFrame):
        """Cancel the output transport."""
        if self._params.audio_out_enabled:
            await self._bridge_audio_queue.put(None)
        else:
            await self._bridge_text_queue.put(None)
        await super().cancel(frame)

    async def write_audio_frame(self, frame: OutputAudioRawFrame) -> bool:
        """Write an audio frame to the bridge queue."""
        input_frame = InputAudioRawFrame(
            audio=frame.audio,
            sample_rate=frame.sample_rate,
            num_channels=frame.num_channels,
        )
        await self._bridge_audio_queue.put(input_frame)
        return True

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames - handle both audio and text frames."""
        await super().process_frame(frame, direction)

        # Handle text frames for text-only mode
        if not self._params.audio_out_enabled:
            # Buffer LLM text frames as they stream in
            if isinstance(frame, LLMTextFrame):
                self._text_buffer.append(frame.text)

            # Emit complete transcription when LLM response ends
            elif isinstance(frame, LLMFullResponseEndFrame):
                if self._text_buffer:
                    # Combine all buffered text into a single transcription
                    full_text = "".join(self._text_buffer)
                    transcription_frame = TranscriptionFrame(
                        text=full_text, user_id="", timestamp=""
                    )
                    await self._bridge_text_queue.put(transcription_frame)
                    # Clear buffer for next response
                    self._text_buffer.clear()


class VoicegroundBridgeTransport(BaseTransport):
    """Transport that connects two Pipecat pipelines for simulation.

    Drop-in replacement for LocalAudioTransport, WebsocketTransport, or SmallWebRTCTransport
    for audio-only bots. Supports on_client_connected/on_client_disconnected events.

    Note: This transport does not support video frames or app messages.
    """

    def __init__(
        self,
        params: VoicegroundBridgeTransportParams | None = None,
        *,
        paired_audio_queue_in: Optional["asyncio.Queue[InputAudioRawFrame | None]"] = None,
        paired_audio_queue_out: Optional["asyncio.Queue[InputAudioRawFrame | None]"] = None,
        paired_text_queue_in: Optional["asyncio.Queue[TranscriptionFrame | None]"] = None,
        paired_text_queue_out: Optional["asyncio.Queue[TranscriptionFrame | None]"] = None,
    ):
        super().__init__()

        self._params = params or VoicegroundBridgeTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        )

        if paired_audio_queue_in is None and paired_audio_queue_out is None:
            self._audio_queue_in: asyncio.Queue[InputAudioRawFrame | None] = asyncio.Queue()
            self._audio_queue_out: asyncio.Queue[InputAudioRawFrame | None] = asyncio.Queue()
            self._text_queue_in: asyncio.Queue[TranscriptionFrame | None] = asyncio.Queue()
            self._text_queue_out: asyncio.Queue[TranscriptionFrame | None] = asyncio.Queue()
            self._is_primary = True
        else:
            assert paired_audio_queue_in is not None
            assert paired_audio_queue_out is not None
            assert paired_text_queue_in is not None
            assert paired_text_queue_out is not None
            self._audio_queue_in = paired_audio_queue_in
            self._audio_queue_out = paired_audio_queue_out
            self._text_queue_in = paired_text_queue_in
            self._text_queue_out = paired_text_queue_out
            self._is_primary = False

        self._input: VoicegroundBridgeInputTransport | None = None
        self._output: VoicegroundBridgeOutputTransport | None = None
        self._observers: list[BaseObserver] = (
            params.observers if params and params.observers else []
        )

        self._register_event_handler("on_client_connected")
        self._register_event_handler("on_client_disconnected")

    def input(self) -> FrameProcessor:
        """Get the input transport."""
        if not self._input:
            self._input = VoicegroundBridgeInputTransport(
                self,
                self._params,
                audio_queue=self._audio_queue_in,
                text_queue=self._text_queue_in,
                name="VoicegroundBridgeInput",
            )
        return self._input

    def output(self) -> FrameProcessor:
        """Get the output transport."""
        if not self._output:
            self._output = VoicegroundBridgeOutputTransport(
                self._params,
                audio_queue=self._audio_queue_out,
                text_queue=self._text_queue_out,
                name="VoicegroundBridgeOutput",
            )
        return self._output

    def create_paired_transport(
        self,
        params: VoicegroundBridgeTransportParams | None = None,
    ) -> "VoicegroundBridgeTransport":
        """Create a paired transport with swapped input/output queues."""
        if not self._is_primary:
            raise RuntimeError("Cannot create paired transport from a paired transport")

        return VoicegroundBridgeTransport(
            params=params or self._params,
            paired_audio_queue_in=self._audio_queue_out,
            paired_audio_queue_out=self._audio_queue_in,
            paired_text_queue_in=self._text_queue_out,
            paired_text_queue_out=self._text_queue_in,
        )

    async def close(self) -> None:
        """Clean up resources."""
        if self._is_primary:
            # Use put_nowait to avoid blocking if queues are full or consumers are dead
            try:
                self._audio_queue_in.put_nowait(None)
            except asyncio.QueueFull:
                pass  # Queue full, consumers likely dead
            try:
                self._audio_queue_out.put_nowait(None)
            except asyncio.QueueFull:
                pass  # Queue full, consumers likely dead
            try:
                self._text_queue_in.put_nowait(None)
            except asyncio.QueueFull:
                pass  # Queue full, consumers likely dead
            try:
                self._text_queue_out.put_nowait(None)
            except asyncio.QueueFull:
                pass  # Queue full, consumers likely dead
