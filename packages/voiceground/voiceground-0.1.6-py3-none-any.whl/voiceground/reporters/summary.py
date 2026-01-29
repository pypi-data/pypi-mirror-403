"""Reporter for collecting simulation summary (transcript, events, evaluations)."""

from dataclasses import dataclass

from voiceground.evaluations import EvaluationResult
from voiceground.events import VoicegroundEvent
from voiceground.reporters.base import BaseReporter


@dataclass
class VoicegroundTranscriptEntry:
    """A single entry in the conversation transcript.

    Attributes:
        role: Either "user" (simulator) or "bot".
        text: The transcribed text.
        timestamp: Timestamp in seconds from simulation start.
    """

    role: str
    text: str
    timestamp: float


class TranscriptCollector:
    """Collects transcript entries from events."""

    def __init__(self):
        self.entries: list[VoicegroundTranscriptEntry] = []
        self._start_time: float | None = None

    def on_event(self, event: VoicegroundEvent) -> None:
        """Process an event and extract transcript if available.

        Note: This runs on the BOT pipeline, observing from the bot's perspective:
        - STT processes what the USER says (user's audio → bot's ears)
        - LLM generates what the BOT says
        """
        if self._start_time is None:
            self._start_time = event.timestamp

        # STT end = user's speech transcribed by bot
        if event.category.value == "stt" and event.type.value == "end":
            text = event.data.get("text", "")
            if text:
                self.entries.append(
                    VoicegroundTranscriptEntry(
                        role="user",  # User's speech heard by bot
                        text=text,
                        timestamp=event.timestamp - (self._start_time or 0),
                    )
                )

        # LLM end = bot's response
        if event.category.value == "llm" and event.type.value == "end":
            text = event.data.get("text", "")
            if text:
                self.entries.append(
                    VoicegroundTranscriptEntry(
                        role="bot",  # Bot's speech
                        text=text,
                        timestamp=event.timestamp - (self._start_time or 0),
                    )
                )


class SummaryReporter(BaseReporter):
    """Reporter that collects events, transcript, and evaluations as a summary.

    This reporter collects all conversation data (transcript, events, evaluations)
    and provides a comprehensive summary of what happened during the conversation.

    You can use this reporter with VoicegroundObserver to collect summary data:

    ```python
    # Create reporter to collect summary
    summary_reporter = SummaryReporter()
    observer = VoicegroundObserver(reporters=[summary_reporter])

    # After conversation
    print(f"Transcript: {len(summary_reporter.transcript_collector.entries)} messages")
    print(f"Duration: {summary_reporter.duration_seconds:.2f}s")
    ```
    """

    def __init__(self):
        self.events: list[VoicegroundEvent] = []
        self.transcript_collector = TranscriptCollector()
        self.evaluations: list[EvaluationResult] = []
        self._conversation_id: str = ""
        self._start_time: float | None = None
        self._end_time: float | None = None

    @property
    def duration_seconds(self) -> float:
        """Get the conversation duration in seconds."""
        if self._start_time is None:
            return 0.0
        end = self._end_time if self._end_time is not None else self._start_time
        return end - self._start_time

    async def on_start(self, conversation_id: str) -> None:
        """Handle simulation start."""
        import time

        self._conversation_id = conversation_id
        self._start_time = time.time()

    async def on_event(self, event: VoicegroundEvent) -> None:
        """Collect events and build transcript."""
        self.events.append(event)
        self.transcript_collector.on_event(event)

    async def on_evaluations(self, evaluations: list[EvaluationResult]) -> None:
        """Store evaluation results."""
        self.evaluations = evaluations

    async def on_end(self) -> None:
        """Handle simulation end."""
        import time

        self._end_time = time.time()
