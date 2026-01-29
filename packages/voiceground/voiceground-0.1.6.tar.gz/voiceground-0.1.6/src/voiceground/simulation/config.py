"""Configuration for call simulation."""

from dataclasses import dataclass, field

from pipecat.observers.base_observer import BaseObserver
from pipecat.services.llm_service import LLMService
from pipecat.services.stt_service import STTService
from pipecat.services.tts_service import TTSService

DEFAULT_SYSTEM_PROMPT_TEMPLATE = """# Scenario
{scenario}

# Instructions:
- Keep your responses natural and conversational, you are a human.
- Speak only what you would say aloud in a real conversation.
- Do NOT use asterisks, stage directions, or narrate actions.
- Let the other side lead the conversation."""

DEFAULT_SYSTEM_PROMPT_WITH_TERMINATION_TEMPLATE = """# Scenario
{scenario}

# The conversation is considered complete when:
{termination_criteria}

# Instructions:
- Keep your responses natural and conversational, you are a human.
- Speak only what you would say aloud in a real conversation.
- Do NOT use asterisks, stage directions, or narrate actions.
- Let the other side lead the conversation.
- Call end_simulation when the conversation is complete and termination criteria is met.
- You are not allowed to answer any follow up questions, or continue the conversation once the termination criteria is met."""


@dataclass
class VoicegroundSimulatorConfig:
    """Configuration for the simulator pipeline.

    The simulator acts as a "fake user" that has a conversation with your bot.

    Attributes:
        llm: LLM service for generating user responses.
        tts: TTS service for generating user voice (required if use_voice is True).
        stt: STT service for transcribing bot speech (required if use_voice is True).
        scenario: Description of the simulation scenario (e.g., "You are a customer calling to book a table for 2 people tomorrow at 7pm").
        use_voice: If True, uses audio with STT/TTS. If False, performs text-only simulation.
        termination_criteria: When the simulation should end naturally (e.g., "A reservation is confirmed by the resturant.").
        system_prompt_template: Template for building the system prompt. Use {scenario} and {termination_criteria} placeholders.
        initiate_conversation: If True, simulator speaks first when bot connects.
        max_turns: Maximum conversation turns before terminating.
        timeout_seconds: Maximum simulation duration in seconds.
        observers: List of observers to attach to the bot pipeline.
    """

    llm: LLMService
    scenario: str
    tts: TTSService | None = None
    stt: STTService | None = None
    use_voice: bool = True
    termination_criteria: str = ""
    system_prompt_template: str = ""
    initiate_conversation: bool = False
    max_turns: int = 10
    timeout_seconds: float = 120.0
    observers: list[BaseObserver] = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.use_voice:
            if self.tts is None:
                raise ValueError("tts service is required when use_voice is True")
            if self.stt is None:
                raise ValueError("stt service is required when use_voice is True")

    @property
    def system_prompt(self) -> str:
        """Build the complete system prompt from the template."""
        # Use custom template if provided, otherwise use default based on termination_criteria
        if self.system_prompt_template:
            template = self.system_prompt_template
        elif self.termination_criteria:
            template = DEFAULT_SYSTEM_PROMPT_WITH_TERMINATION_TEMPLATE
        else:
            template = DEFAULT_SYSTEM_PROMPT_TEMPLATE

        return template.format(
            scenario=self.scenario,
            termination_criteria=self.termination_criteria if self.termination_criteria else "",
        ).strip()
