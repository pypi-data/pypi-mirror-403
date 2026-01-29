"""MetricsReporter - Generate MetricsFrame objects from conversation events."""

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from pipecat.frames.frames import MetricsFrame
from pydantic import BaseModel

from voiceground.events import EventCategory, EventType, VoicegroundEvent
from voiceground.metrics import (
    VoicegroundLLMResponseTimeFrame,
    VoicegroundResponseTimeFrame,
    VoicegroundSystemOverheadFrame,
    VoicegroundToolUsageFrame,
    VoicegroundTranscriptionOverheadFrame,
    VoicegroundTurnDurationFrame,
    VoicegroundVoiceSynthesisOverheadFrame,
)
from voiceground.reporters.base import BaseReporter


class ToolCallData(BaseModel):
    """Type-safe model for tool call data.

    Attributes:
        name: Name of the tool/function that was called.
        duration: Duration of the tool call in milliseconds.
    """

    name: str
    duration: float


class SystemOverheadData(BaseModel):
    """Type-safe model for system overhead data.

    Attributes:
        name: Name/type of the system operation (e.g., "context_aggregation_timeout").
        duration: Duration of the system operation in milliseconds.
    """

    name: str
    duration: float


class TurnMetricsData(BaseModel):
    """Type-safe model for calculated turn metrics.

    Attributes:
        turn_duration: Total turn duration in milliseconds.
        response_time: Response time in milliseconds (or None).
        transcription_overhead: Transcription overhead in milliseconds (or None).
        voice_synthesis_overhead: Voice synthesis overhead in milliseconds (or None).
        llm_response_time: LLM response time in milliseconds (or None).
        llm_net_time: LLM net time (without tools) in milliseconds (or None).
        system_overheads: List of individual system overhead data.
        tool_calls: List of individual tool call data.
    """

    turn_duration: float
    response_time: float | None
    transcription_overhead: float | None
    voice_synthesis_overhead: float | None
    llm_response_time: float | None
    llm_net_time: float | None
    system_overheads: list[SystemOverheadData]
    tool_calls: list[ToolCallData]


# Pure functional helpers for event processing


def find_event(
    events: list[VoicegroundEvent], category: EventCategory, event_type: EventType
) -> VoicegroundEvent | None:
    """Find the first event matching category and type."""
    return next(
        (e for e in events if e.category == category and e.type == event_type),
        None,
    )


def find_all_events(
    events: list[VoicegroundEvent], category: EventCategory, event_type: EventType
) -> list[VoicegroundEvent]:
    """Find all events matching category and type."""
    return [e for e in events if e.category == category and e.type == event_type]


def calculate_duration_ms(
    start: VoicegroundEvent | None, end: VoicegroundEvent | None
) -> float | None:
    """Calculate duration between two events in milliseconds."""
    if start and end:
        return (end.timestamp - start.timestamp) * 1000
    return None


def extract_operation_name(start_event: VoicegroundEvent, end_event: VoicegroundEvent) -> str:
    """Extract operation name from event data, with fallback."""
    return (
        end_event.data.get("operation", "")
        or start_event.data.get("operation", "")
        or "unknown_operation"
    )


def find_matching_end_event(
    events: list[VoicegroundEvent],
    start_event: VoicegroundEvent,
    category: EventCategory,
    min_timestamp: float,
    max_timestamp: float,
) -> VoicegroundEvent | None:
    """Find the matching end event for a start event within a time range."""
    return next(
        (
            e
            for e in events
            if e.category == category
            and e.type == EventType.END
            and e.timestamp > start_event.timestamp
            and min_timestamp <= e.timestamp <= max_timestamp
        ),
        None,
    )


def calculate_tool_calls(
    events: list[VoicegroundEvent], llm_start: VoicegroundEvent, llm_end: VoicegroundEvent
) -> list[ToolCallData]:
    """Calculate individual tool calls that start during LLM phase.

    Tool calls can start during the LLM phase and may end after the LLM phase ends.
    """
    tool_call_starts = [
        e
        for e in find_all_events(events, EventCategory.TOOL_CALL, EventType.START)
        if llm_start.timestamp <= e.timestamp <= llm_end.timestamp
    ]

    tool_calls = []
    used_end_events = set()

    for start_event in tool_call_starts:
        # Find matching end event - it can be after llm_end
        # Use a large max_timestamp to allow tool calls to end after LLM phase
        end_event = next(
            (
                e
                for e in events
                if e.id not in used_end_events
                and e.category == EventCategory.TOOL_CALL
                and e.type == EventType.END
                and e.timestamp > start_event.timestamp
                and (
                    (e.data.get("operation") == start_event.data.get("operation"))
                    or (e.data.get("name") == start_event.data.get("name"))
                )
            ),
            None,
        )

        if end_event:
            used_end_events.add(end_event.id)
            duration_ms = calculate_duration_ms(start_event, end_event)
            if duration_ms is not None:
                tool_name = extract_operation_name(start_event, end_event).replace(
                    "unknown_operation", "unknown_tool"
                )
                tool_calls.append(ToolCallData(name=tool_name, duration=duration_ms))

    return tool_calls


def calculate_system_overheads(
    events: list[VoicegroundEvent], stt_end: VoicegroundEvent, llm_start: VoicegroundEvent
) -> list[SystemOverheadData]:
    """Calculate individual system overheads between stt:end and llm:start."""
    system_starts = [
        e
        for e in find_all_events(events, EventCategory.SYSTEM, EventType.START)
        if stt_end.timestamp <= e.timestamp <= llm_start.timestamp
    ]

    system_overheads = []
    for start_event in system_starts:
        end_event = find_matching_end_event(
            events, start_event, EventCategory.SYSTEM, stt_end.timestamp, llm_start.timestamp
        )
        if end_event:
            duration_ms = calculate_duration_ms(start_event, end_event)
            if duration_ms is not None:
                operation_name = extract_operation_name(start_event, end_event)
                system_overheads.append(
                    SystemOverheadData(name=operation_name, duration=duration_ms)
                )

    return system_overheads


def calculate_response_time(
    events: list[VoicegroundEvent],
    user_speak_end: VoicegroundEvent | None,
    bot_speak_start: VoicegroundEvent | None,
) -> float | None:
    """Calculate response time from user_speak:end to bot_speak:start."""
    if user_speak_end and bot_speak_start:
        return calculate_duration_ms(user_speak_end, bot_speak_start)

    if not user_speak_end and bot_speak_start:
        first_event_time = min((e.timestamp for e in events), default=0.0)
        return (bot_speak_start.timestamp - first_event_time) * 1000

    return None


def calculate_llm_net_time(
    llm_response_time: float | None, tools_total_duration: float
) -> float | None:
    """Calculate LLM net time (response time minus tools overhead)."""
    if llm_response_time is None:
        return None

    if tools_total_duration > 0:
        return llm_response_time - tools_total_duration

    # If no tools, net time equals total time
    return llm_response_time


def calculate_turn_metrics(events: list[VoicegroundEvent]) -> TurnMetricsData:
    """Calculate all metrics for a turn from events."""
    # Find key events
    user_speak_end = find_event(events, EventCategory.USER_SPEAK, EventType.END)
    stt_end = find_event(events, EventCategory.STT, EventType.END)
    llm_first_byte = find_event(events, EventCategory.LLM, EventType.FIRST_BYTE)
    tts_start = find_event(events, EventCategory.TTS, EventType.START)
    bot_speak_start = find_event(events, EventCategory.BOT_SPEAK, EventType.START)

    # Use the first LLM start for metrics
    llm_starts = find_all_events(events, EventCategory.LLM, EventType.START)
    llm_start = min(llm_starts, key=lambda e: e.timestamp) if llm_starts else None
    llm_end = find_event(events, EventCategory.LLM, EventType.END)

    # Calculate time ranges
    first_event_time = min((e.timestamp for e in events), default=0.0)
    last_event_time = max((e.timestamp for e in events), default=0.0)
    turn_duration_ms = (last_event_time - first_event_time) * 1000

    # Calculate metrics
    response_time = calculate_response_time(events, user_speak_end, bot_speak_start)
    transcription_overhead = calculate_duration_ms(user_speak_end, stt_end)
    voice_synthesis_overhead = calculate_duration_ms(tts_start, bot_speak_start)
    llm_response_time = calculate_duration_ms(llm_start, llm_first_byte)

    # Calculate tool calls and system overheads
    tool_calls = calculate_tool_calls(events, llm_start, llm_end) if llm_start and llm_end else []
    tools_total_duration = sum(tc.duration for tc in tool_calls)
    llm_net_time = calculate_llm_net_time(llm_response_time, tools_total_duration)

    system_overheads = (
        calculate_system_overheads(events, stt_end, llm_start) if stt_end and llm_start else []
    )

    return TurnMetricsData(
        turn_duration=turn_duration_ms,
        response_time=response_time,
        transcription_overhead=transcription_overhead,
        voice_synthesis_overhead=voice_synthesis_overhead,
        llm_response_time=llm_response_time,
        llm_net_time=llm_net_time,
        system_overheads=system_overheads,
        tool_calls=tool_calls,
    )


# Pure functional helpers for metric frame creation


def create_all_metric_frames(metrics: TurnMetricsData) -> list[MetricsFrame]:
    """Create all MetricsFrame objects for a turn's metrics."""
    frames: list[MetricsFrame] = []

    # Turn duration (always present)
    frames.append(VoicegroundTurnDurationFrame(value=metrics.turn_duration / 1000))

    # Optional metrics
    if metrics.response_time is not None:
        frames.append(VoicegroundResponseTimeFrame(value=metrics.response_time / 1000))

    if metrics.transcription_overhead is not None:
        frames.append(
            VoicegroundTranscriptionOverheadFrame(value=metrics.transcription_overhead / 1000)
        )

    if metrics.voice_synthesis_overhead is not None:
        frames.append(
            VoicegroundVoiceSynthesisOverheadFrame(value=metrics.voice_synthesis_overhead / 1000)
        )

    if metrics.llm_response_time is not None:
        frames.append(
            VoicegroundLLMResponseTimeFrame(
                value=metrics.llm_response_time / 1000,
                net_value=metrics.llm_net_time / 1000 if metrics.llm_net_time is not None else None,
            )
        )

    # System overheads
    for so in metrics.system_overheads:
        frames.append(
            VoicegroundSystemOverheadFrame(
                value=so.duration / 1000,
                operation_name=so.name,
            )
        )

    # Tool usage
    for tc in metrics.tool_calls:
        frames.append(
            VoicegroundToolUsageFrame(
                value=tc.duration / 1000,
                tool_name=tc.name,
            )
        )

    return frames


class MetricsReporter(BaseReporter):
    """Reporter that creates MetricsFrame objects from conversation events.

    Calculates opinionated metrics per turn and creates MetricsFrame objects
    with custom Voiceground metric classes. Supports an optional callback
    for real-time metric processing (e.g., for Prometheus integration).

    Args:
        on_metric_reported: Optional callback function called immediately after
            each MetricsFrame is created. Can be sync or async.
            Signature: Callable[[MetricsFrame], Awaitable[None] | None]
    """

    def __init__(
        self,
        on_metric_reported: Callable[[MetricsFrame], Awaitable[None] | None] | None = None,
    ):
        self._events: list[VoicegroundEvent] = []
        self._metrics_frames: list[MetricsFrame] = []
        self._on_metric_reported = on_metric_reported
        self._conversation_id: str | None = None

    async def on_start(self, conversation_id: str) -> None:
        """Set the conversation ID when the pipeline starts."""
        self._conversation_id = conversation_id
        self._events = []
        self._metrics_frames = []

    async def on_event(self, event: VoicegroundEvent) -> None:
        """Record an event."""
        self._events.append(event)

    async def on_end(self) -> None:
        """Calculate metrics and create MetricsFrame objects."""
        if not self._events:
            return

        turns = self._parse_turns(self._events)

        for turn in turns:
            metrics = calculate_turn_metrics(turn["events"])
            await self._create_metrics_frames(metrics, turn["turn_id"])

    def get_metrics_frames(self) -> list[MetricsFrame]:
        """Get all generated MetricsFrame objects.

        Returns:
            List of MetricsFrame objects, one per metric per turn.
        """
        return self._metrics_frames.copy()

    def _parse_turns(self, events: list[VoicegroundEvent]) -> list[dict[str, Any]]:
        """Parse events into turns, matching UI logic from TurnsView.tsx."""
        if not events:
            return []

        sorted_events = sorted(events, key=lambda e: e.timestamp)
        turns: list[dict[str, Any]] = []
        current_turn: dict[str, Any] | None = None
        turn_id = 0

        for event in sorted_events:
            if event.category == EventCategory.USER_SPEAK and event.type == EventType.START:
                if current_turn:
                    # Close the current turn
                    if current_turn["events"]:
                        current_turn["end_time"] = current_turn["events"][-1].timestamp
                    turns.append(current_turn)
                current_turn = {
                    "turn_id": turn_id,
                    "start_time": event.timestamp,
                    "end_time": event.timestamp,
                    "events": [event],
                }
                turn_id += 1
            elif current_turn:
                # Check if this event belongs to the previous turn
                if (
                    event.category == EventCategory.BOT_SPEAK
                    and event.type == EventType.END
                    and turns
                ):
                    last_turn = turns[-1]
                    if event.timestamp - last_turn["end_time"] < 0.1:
                        last_turn["events"].append(event)
                        last_turn["end_time"] = event.timestamp
                        continue

                current_turn["events"].append(event)
                current_turn["end_time"] = event.timestamp

                if event.category == EventCategory.BOT_SPEAK and event.type == EventType.END:
                    turns.append(current_turn)
                    current_turn = None
            else:
                # If no current turn and no turns yet, start a turn on the first event
                if not turns:
                    current_turn = {
                        "turn_id": turn_id,
                        "start_time": event.timestamp,
                        "end_time": event.timestamp,
                        "events": [event],
                    }
                    turn_id += 1
                else:
                    # Try to add to the last turn if within 2 seconds
                    last_turn = turns[-1]
                    if event.timestamp - last_turn["end_time"] < 2:
                        last_turn["events"].append(event)
                        last_turn["end_time"] = event.timestamp

        if current_turn:
            turns.append(current_turn)

        return turns

    async def _create_metrics_frames(self, metrics: TurnMetricsData, turn_id: int) -> None:
        """Create MetricsFrame objects for all metrics and call callback if provided."""
        metric_frames = create_all_metric_frames(metrics)

        for metrics_frame in metric_frames:
            self._metrics_frames.append(metrics_frame)

            if self._on_metric_reported:
                await self._invoke_callback(metrics_frame)

    async def _invoke_callback(self, metrics_frame: MetricsFrame) -> None:
        """Invoke the callback function, handling both sync and async cases."""
        if self._on_metric_reported is None:
            return

        if inspect.iscoroutinefunction(self._on_metric_reported):
            await self._on_metric_reported(metrics_frame)
        else:
            result = self._on_metric_reported(metrics_frame)
            if inspect.isawaitable(result):
                await result
