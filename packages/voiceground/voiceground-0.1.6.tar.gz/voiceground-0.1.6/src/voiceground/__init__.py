"""Voiceground - Observability framework for Pipecat conversational AI."""

# Simulation module (import the submodule for convenience)
from voiceground import simulation
from voiceground.evaluations import (
    BaseEvaluator,
    EvaluationDefinition,
    EvaluationResult,
    EvaluationType,
    OpenAIEvaluator,
)
from voiceground.events import VoicegroundEvent
from voiceground.metrics import (
    VoicegroundLLMResponseTimeFrame,
    VoicegroundResponseTimeFrame,
    VoicegroundSystemOverheadFrame,
    VoicegroundToolUsageFrame,
    VoicegroundTranscriptionOverheadFrame,
    VoicegroundTurnDurationFrame,
    VoicegroundVoiceSynthesisOverheadFrame,
)
from voiceground.observer import VoicegroundObserver
from voiceground.reporters import BaseReporter, HTMLReporter, MetricsReporter, SummaryReporter

try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("voiceground")
except (PackageNotFoundError, Exception):
    # Fallback for development/editable installs
    # The actual version will be set by hatch-vcs during build
    __version__ = "0.0.0+dev"
__all__ = [
    # Core
    "VoicegroundObserver",
    "VoicegroundEvent",
    # Reporters
    "BaseReporter",
    "HTMLReporter",
    "MetricsReporter",
    "SummaryReporter",
    # Evaluations
    "BaseEvaluator",
    "OpenAIEvaluator",
    "EvaluationDefinition",
    "EvaluationResult",
    "EvaluationType",
    # Metrics frames
    "VoicegroundTurnDurationFrame",
    "VoicegroundResponseTimeFrame",
    "VoicegroundTranscriptionOverheadFrame",
    "VoicegroundVoiceSynthesisOverheadFrame",
    "VoicegroundLLMResponseTimeFrame",
    "VoicegroundSystemOverheadFrame",
    "VoicegroundToolUsageFrame",
    # Simulation
    "simulation",
    # Version
    "__version__",
]
