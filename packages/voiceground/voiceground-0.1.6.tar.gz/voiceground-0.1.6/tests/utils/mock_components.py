"""Mock components for testing Voiceground simulations."""

from pipecat.frames.frames import (
    Frame,
    LLMContextFrame,
    LLMFullResponseEndFrame,
    LLMRunFrame,
    LLMTextFrame,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.llm_service import LLMService
from pipecat.services.stt_service import STTService
from pipecat.services.tts_service import TTSService

from voiceground.evaluations import BaseEvaluator


class MockSTTService(STTService):
    """Mock STT service for testing."""

    def __init__(self):
        super().__init__()

    async def run_stt(self, audio):
        """Mock STT implementation."""
        pass


class MockLLMService(LLMService):
    """Mock LLM service for testing with predetermined responses.

    This service responds to the same triggers as real LLM services
    (LLMRunFrame, LLMContextFrame) and cycles through a list of responses.
    """

    def __init__(self, responses: list[str] | None = None):
        """Initialize with a list of responses to cycle through.

        Args:
            responses: List of text responses. Each trigger will return the next response.
        """
        if responses is None:
            responses = []
        super().__init__()
        self._responses = responses
        self._current_index = 0

    async def _process_context(self, context):
        """Process context and return the next predetermined response."""
        # Get next response
        if self._current_index >= len(self._responses):
            response = ""  # No more responses
        else:
            response = self._responses[self._current_index]
            self._current_index += 1

        # Push the context frame through
        await self.push_frame(context)

        if response:
            # Simulate streaming response token by token (split by spaces for readability)
            words = response.split()
            for i, word in enumerate(words):
                # Add space before word (except first)
                text = f" {word}" if i > 0 else word
                await self.push_frame(LLMTextFrame(text=text))

            await self.push_frame(LLMFullResponseEndFrame())

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames - respond to LLM trigger frames and pass through others."""
        await super().process_frame(frame, direction)

        # Respond to the same triggers as real LLM services
        if isinstance(frame, (LLMContextFrame, LLMRunFrame)):
            await self._process_context(frame)
        else:
            # Pass through all other frames so they don't get blocked
            await self.push_frame(frame, direction)


class MockTTSService(TTSService):
    """Mock TTS service for testing."""

    def __init__(self):
        super().__init__(sample_rate=16000)
        self._sample_rate = 16000

    async def run_tts(self, text: str):
        """Mock TTS implementation."""
        pass


class MockEvaluator(BaseEvaluator):
    """Mock evaluator for testing evaluations."""

    def __init__(self, response: str):
        """Initialize with a predetermined JSON response.

        Args:
            response: JSON string response to return (e.g., '{"passed": true, "reasoning": "..."}').
        """
        self._response = response

    async def evaluate(self, prompt: str) -> str:
        """Return the predetermined response."""
        return self._response
