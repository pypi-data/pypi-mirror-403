"""Tests for MetricsReporter."""

import uuid

import pytest

from voiceground.events import EventCategory, EventType, VoicegroundEvent
from voiceground.metrics import (
    LLMResponseTimeMetricsData,
    ResponseTimeMetricsData,
    SystemOverheadMetricsData,
    ToolUsageMetricsData,
    TranscriptionOverheadMetricsData,
    TurnDurationMetricsData,
    VoiceSynthesisOverheadMetricsData,
)
from voiceground.reporters import MetricsReporter


class TestMetricsReporter:
    """Tests for MetricsReporter."""

    @pytest.mark.asyncio
    async def test_basic_metrics_calculation(self):
        """Test that metrics are calculated correctly for a simple turn."""
        reporter = MetricsReporter()
        conversation_id = str(uuid.uuid4())

        await reporter.on_start(conversation_id)

        # Create a simple turn: user speaks, STT, LLM, TTS, bot speaks
        base_time = 1000.0
        events = [
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time,
                category=EventCategory.USER_SPEAK,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.0,
                category=EventCategory.USER_SPEAK,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.5,
                category=EventCategory.STT,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.0,
                category=EventCategory.LLM,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.5,
                category=EventCategory.LLM,
                type=EventType.FIRST_BYTE,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 3.0,
                category=EventCategory.LLM,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 3.5,
                category=EventCategory.TTS,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 4.0,
                category=EventCategory.BOT_SPEAK,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 5.0,
                category=EventCategory.BOT_SPEAK,
                type=EventType.END,
            ),
        ]

        for event in events:
            await reporter.on_event(event)

        await reporter.on_end()

        metrics_frames = reporter.get_metrics_frames()
        assert len(metrics_frames) > 0

        # Check that we have metrics for the turn
        metric_types = {type(frame.data[0]).__name__ for frame in metrics_frames}

        assert "TurnDurationMetricsData" in metric_types
        assert "ResponseTimeMetricsData" in metric_types
        assert "TranscriptionOverheadMetricsData" in metric_types
        assert "LLMResponseTimeMetricsData" in metric_types
        assert "VoiceSynthesisOverheadMetricsData" in metric_types

        # Verify that each MetricsFrame has a name attribute
        for frame in metrics_frames:
            assert hasattr(frame, "name")
            assert isinstance(frame.name, str)
            # Check name is valid (can be turn metrics or tool_usage_*)
            assert (
                frame.name
                in [
                    "turn_duration",
                    "response_time",
                    "transcription_overhead",
                    "voice_synthesis_overhead",
                    "llm_response_time",
                ]
                or frame.name.startswith("tool_usage_")
                or frame.name.startswith("system_overhead_")
            )

    @pytest.mark.asyncio
    async def test_individual_tool_usage_calculation(self):
        """Test that individual tool usage metrics are calculated correctly."""
        reporter = MetricsReporter()
        conversation_id = str(uuid.uuid4())

        await reporter.on_start(conversation_id)

        # Create a turn with tool calls during LLM phase
        base_time = 1000.0
        events = [
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time,
                category=EventCategory.USER_SPEAK,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.0,
                category=EventCategory.USER_SPEAK,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.5,
                category=EventCategory.STT,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.0,
                category=EventCategory.LLM,
                type=EventType.START,
            ),
            # Tool call 1: get_weather, 0.2 seconds
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.1,
                category=EventCategory.TOOL_CALL,
                type=EventType.START,
                data={"operation": "get_weather"},
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.3,
                category=EventCategory.TOOL_CALL,
                type=EventType.END,
                data={"operation": "get_weather"},
            ),
            # Tool call 2: get_time, 0.3 seconds
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.4,
                category=EventCategory.TOOL_CALL,
                type=EventType.START,
                data={"operation": "get_time"},
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.7,
                category=EventCategory.TOOL_CALL,
                type=EventType.END,
                data={"operation": "get_time"},
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 3.0,
                category=EventCategory.LLM,
                type=EventType.FIRST_BYTE,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 3.5,
                category=EventCategory.LLM,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 4.0,
                category=EventCategory.BOT_SPEAK,
                type=EventType.START,
            ),
        ]

        for event in events:
            await reporter.on_event(event)

        await reporter.on_end()

        metrics_frames = reporter.get_metrics_frames()
        tool_metrics = [
            frame for frame in metrics_frames if isinstance(frame.data[0], ToolUsageMetricsData)
        ]

        # Should have 2 individual tool metrics
        assert len(tool_metrics) == 2

        # Check tool names and durations
        tool_names = {frame.data[0].tool_name for frame in tool_metrics}
        assert "get_weather" in tool_names
        assert "get_time" in tool_names

        # Check durations
        for frame in tool_metrics:
            metric = frame.data[0]
            if metric.tool_name == "get_weather":
                assert abs(metric.value - 0.2) < 0.01
            elif metric.tool_name == "get_time":
                assert abs(metric.value - 0.3) < 0.01

    @pytest.mark.asyncio
    async def test_callback_invocation_sync(self):
        """Test that sync callback is called for each metric."""
        callback_calls = []

        def sync_callback(metrics_frame):
            callback_calls.append(metrics_frame)

        reporter = MetricsReporter(on_metric_reported=sync_callback)
        conversation_id = str(uuid.uuid4())

        await reporter.on_start(conversation_id)

        base_time = 1000.0
        events = [
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time,
                category=EventCategory.USER_SPEAK,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.0,
                category=EventCategory.USER_SPEAK,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.5,
                category=EventCategory.STT,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.0,
                category=EventCategory.LLM,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.5,
                category=EventCategory.LLM,
                type=EventType.FIRST_BYTE,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 3.0,
                category=EventCategory.BOT_SPEAK,
                type=EventType.START,
            ),
        ]

        for event in events:
            await reporter.on_event(event)

        await reporter.on_end()

        # Callback should have been called for each metric
        assert len(callback_calls) > 0
        # Verify all callback calls are MetricsFrame objects with Voiceground metrics
        for call in callback_calls:
            assert hasattr(call, "data")
            assert len(call.data) > 0
            assert isinstance(
                call.data[0],
                (
                    TurnDurationMetricsData,
                    ResponseTimeMetricsData,
                    TranscriptionOverheadMetricsData,
                    LLMResponseTimeMetricsData,
                    SystemOverheadMetricsData,
                    VoiceSynthesisOverheadMetricsData,
                    ToolUsageMetricsData,
                ),
            )

    @pytest.mark.asyncio
    async def test_callback_invocation_async(self):
        """Test that async callback is called for each metric."""
        callback_calls = []

        async def async_callback(metrics_frame):
            callback_calls.append(metrics_frame)

        reporter = MetricsReporter(on_metric_reported=async_callback)
        conversation_id = str(uuid.uuid4())

        await reporter.on_start(conversation_id)

        base_time = 1000.0
        events = [
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time,
                category=EventCategory.USER_SPEAK,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.0,
                category=EventCategory.USER_SPEAK,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.5,
                category=EventCategory.STT,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.0,
                category=EventCategory.LLM,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.5,
                category=EventCategory.LLM,
                type=EventType.FIRST_BYTE,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 3.0,
                category=EventCategory.BOT_SPEAK,
                type=EventType.START,
            ),
        ]

        for event in events:
            await reporter.on_event(event)

        await reporter.on_end()

        # Callback should have been called for each metric
        assert len(callback_calls) > 0

    @pytest.mark.asyncio
    async def test_system_overhead_list(self):
        """Test that system overhead metrics are collected as a list with operation names."""
        reporter = MetricsReporter()
        conversation_id = str(uuid.uuid4())

        await reporter.on_start(conversation_id)

        base_time = 1000.0
        events = [
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time,
                category=EventCategory.USER_SPEAK,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.0,
                category=EventCategory.USER_SPEAK,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.5,
                category=EventCategory.STT,
                type=EventType.END,
            ),
            # System overhead 1: context_aggregation_timeout, 0.2 seconds
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.6,
                category=EventCategory.SYSTEM,
                type=EventType.START,
                data={"operation": "context_aggregation_timeout"},
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.8,
                category=EventCategory.SYSTEM,
                type=EventType.END,
                data={"operation": "context_aggregation_timeout"},
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.0,
                category=EventCategory.LLM,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.5,
                category=EventCategory.LLM,
                type=EventType.FIRST_BYTE,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 3.0,
                category=EventCategory.BOT_SPEAK,
                type=EventType.START,
            ),
        ]

        for event in events:
            await reporter.on_event(event)

        await reporter.on_end()

        metrics_frames = reporter.get_metrics_frames()
        system_metrics = [
            frame
            for frame in metrics_frames
            if isinstance(frame.data[0], SystemOverheadMetricsData)
        ]

        # Should have 1 system overhead metric
        assert len(system_metrics) == 1
        system_metric = system_metrics[0].data[0]
        assert system_metric.operation_name == "context_aggregation_timeout"
        assert abs(system_metric.value - 0.2) < 0.01

    @pytest.mark.asyncio
    async def test_llm_net_time_calculation(self):
        """Test that LLM net time (without tools) is calculated correctly."""
        reporter = MetricsReporter()
        conversation_id = str(uuid.uuid4())

        await reporter.on_start(conversation_id)

        base_time = 1000.0
        events = [
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time,
                category=EventCategory.USER_SPEAK,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.0,
                category=EventCategory.USER_SPEAK,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.5,
                category=EventCategory.STT,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.0,
                category=EventCategory.LLM,
                type=EventType.START,
            ),
            # Tool call: 0.2 seconds
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.1,
                category=EventCategory.TOOL_CALL,
                type=EventType.START,
                data={"operation": "get_weather"},
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.3,
                category=EventCategory.TOOL_CALL,
                type=EventType.END,
                data={"operation": "get_weather"},
            ),
            # LLM first byte at 3.0 (total LLM time = 1.0s, tools = 0.2s, net = 0.8s)
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 3.0,
                category=EventCategory.LLM,
                type=EventType.FIRST_BYTE,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 3.5,
                category=EventCategory.LLM,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 4.0,
                category=EventCategory.BOT_SPEAK,
                type=EventType.START,
            ),
        ]

        for event in events:
            await reporter.on_event(event)

        await reporter.on_end()

        metrics_frames = reporter.get_metrics_frames()
        llm_metrics = [
            frame
            for frame in metrics_frames
            if isinstance(frame.data[0], LLMResponseTimeMetricsData)
        ]

        assert len(llm_metrics) == 1
        llm_metric = llm_metrics[0].data[0]
        # Total LLM response time should be 1.0 seconds (3.0 - 2.0)
        assert abs(llm_metric.value - 1.0) < 0.01
        # Net time should be 0.8 seconds (1.0 - 0.2)
        assert llm_metric.net_value is not None
        assert abs(llm_metric.net_value - 0.8) < 0.01

    @pytest.mark.asyncio
    async def test_tool_calls_ending_after_llm_end(self):
        """Test that tool calls ending after llm:end are still captured."""
        reporter = MetricsReporter()
        conversation_id = str(uuid.uuid4())

        await reporter.on_start(conversation_id)

        base_time = 1000.0
        events = [
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time,
                category=EventCategory.USER_SPEAK,
                type=EventType.START,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.0,
                category=EventCategory.USER_SPEAK,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 1.5,
                category=EventCategory.STT,
                type=EventType.END,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.0,
                category=EventCategory.LLM,
                type=EventType.START,
            ),
            # Tool call starts during LLM phase
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.1,
                category=EventCategory.TOOL_CALL,
                type=EventType.START,
                data={"operation": "get_weather"},
            ),
            # LLM ends BEFORE tool call ends (realistic scenario)
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.2,
                category=EventCategory.LLM,
                type=EventType.END,
            ),
            # Tool call ends AFTER llm:end
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.5,
                category=EventCategory.TOOL_CALL,
                type=EventType.END,
                data={"operation": "get_weather"},
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 2.6,
                category=EventCategory.LLM,
                type=EventType.FIRST_BYTE,
            ),
            VoicegroundEvent(
                id=str(uuid.uuid4()),
                timestamp=base_time + 3.0,
                category=EventCategory.BOT_SPEAK,
                type=EventType.START,
            ),
        ]

        for event in events:
            await reporter.on_event(event)

        await reporter.on_end()

        metrics_frames = reporter.get_metrics_frames()
        tool_metrics = [
            frame for frame in metrics_frames if isinstance(frame.data[0], ToolUsageMetricsData)
        ]

        # Should have 1 tool metric even though it ended after llm:end
        assert len(tool_metrics) == 1
        tool_metric = tool_metrics[0].data[0]
        assert tool_metric.tool_name == "get_weather"
        # Duration should be 0.4 seconds (2.5 - 2.1)
        assert abs(tool_metric.value - 0.4) < 0.01
