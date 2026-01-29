"""Voiceground custom metrics frame classes for opinionated metrics."""

from pipecat.frames.frames import MetricsFrame
from pipecat.metrics.metrics import MetricsData


class VoicegroundMetricsData(MetricsData):
    """Base class for all Voiceground metrics data.

    Automatically sets processor="voiceground" for all metrics.
    """

    processor: str = "voiceground"


class TurnDurationMetricsData(VoicegroundMetricsData):
    """Turn Duration metrics data."""

    value: float


class ResponseTimeMetricsData(VoicegroundMetricsData):
    """Response Time metrics data."""

    value: float


class TranscriptionOverheadMetricsData(VoicegroundMetricsData):
    """Transcription Overhead metrics data."""

    value: float


class VoiceSynthesisOverheadMetricsData(VoicegroundMetricsData):
    """Voice Synthesis Overhead metrics data."""

    value: float


class LLMResponseTimeMetricsData(VoicegroundMetricsData):
    """LLM Response Time metrics data."""

    value: float
    net_value: float | None = None


class SystemOverheadMetricsData(VoicegroundMetricsData):
    """System Overhead metrics data."""

    value: float
    operation_name: str


class ToolUsageMetricsData(VoicegroundMetricsData):
    """Tool Usage metrics data."""

    value: float
    tool_name: str


class VoicegroundMetricFrame(MetricsFrame):
    """Base class for all Voiceground metric frames.

    Automatically sets up the MetricsFrame with the metric data and name.
    """

    name: str = ""

    def __init__(self, metric_data: MetricsData, name: str):
        super().__init__(data=[metric_data])
        self.name = name


class VoicegroundTurnDurationFrame(VoicegroundMetricFrame):
    """Turn Duration metric frame: Total time from first event to last event in the turn.

    Parameters:
        value: Turn duration in seconds.
    """

    def __init__(self, value: float):
        metric_data = TurnDurationMetricsData(processor="voiceground", value=value)
        super().__init__(metric_data, "turn_duration")


class VoicegroundResponseTimeFrame(VoicegroundMetricFrame):
    """Response Time metric frame: Time from user_speak:end to bot_speak:start.

    Parameters:
        value: Response time in seconds.
    """

    def __init__(self, value: float):
        metric_data = ResponseTimeMetricsData(processor="voiceground", value=value)
        super().__init__(metric_data, "response_time")


class VoicegroundTranscriptionOverheadFrame(VoicegroundMetricFrame):
    """Transcription Overhead metric frame: Time from user_speak:end to stt:end.

    Parameters:
        value: Transcription overhead in seconds.
    """

    def __init__(self, value: float):
        metric_data = TranscriptionOverheadMetricsData(processor="voiceground", value=value)
        super().__init__(metric_data, "transcription_overhead")


class VoicegroundVoiceSynthesisOverheadFrame(VoicegroundMetricFrame):
    """Voice Synthesis Overhead metric frame: Time from tts:start to bot_speak:start.

    Parameters:
        value: Voice synthesis overhead in seconds.
    """

    def __init__(self, value: float):
        metric_data = VoiceSynthesisOverheadMetricsData(processor="voiceground", value=value)
        super().__init__(metric_data, "voice_synthesis_overhead")


class VoicegroundLLMResponseTimeFrame(VoicegroundMetricFrame):
    """LLM Response Time metric frame: Time from llm:start to llm:first_byte.

    Parameters:
        value: LLM response time in seconds (includes tools overhead).
        net_value: LLM response time in seconds excluding tools overhead.
    """

    def __init__(self, value: float, net_value: float | None = None):
        metric_data = LLMResponseTimeMetricsData(
            processor="voiceground", value=value, net_value=net_value
        )
        super().__init__(metric_data, "llm_response_time")


class VoicegroundSystemOverheadFrame(VoicegroundMetricFrame):
    """System Overhead metric frame: Duration of a specific system operation.

    Parameters:
        value: System overhead in seconds.
        operation_name: Name/type of the system operation (e.g., "context_aggregation_timeout").
    """

    def __init__(self, value: float, operation_name: str):
        metric_data = SystemOverheadMetricsData(
            processor="voiceground", value=value, operation_name=operation_name
        )
        super().__init__(metric_data, f"system_overhead_{operation_name}")


class VoicegroundToolUsageFrame(VoicegroundMetricFrame):
    """Individual Tool Usage metric frame: Duration of a specific tool call.

    Parameters:
        value: Tool call duration in seconds.
        tool_name: Name of the tool/function that was called.
    """

    def __init__(self, value: float, tool_name: str):
        metric_data = ToolUsageMetricsData(
            processor="voiceground", value=value, tool_name=tool_name
        )
        super().__init__(metric_data, f"tool_usage_{tool_name}")
