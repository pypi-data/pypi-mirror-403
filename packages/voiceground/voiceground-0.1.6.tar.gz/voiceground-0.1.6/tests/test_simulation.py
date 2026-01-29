"""Tests for Voiceground simulation feature."""

import pytest

from tests.utils import MockEvaluator, MockLLMService, MockSTTService, MockTTSService, run_mock_bot
from voiceground import SummaryReporter, VoicegroundObserver
from voiceground.evaluations import BooleanEvaluationDefinition, EvaluationType
from voiceground.evaluator import VoicegroundEvaluator
from voiceground.simulation import VoicegroundSimulation, VoicegroundSimulatorConfig


def test_system_prompt_generation():
    """Test that system prompt is correctly generated from template."""

    # Test case constants
    TEST_CASE_SCENARIO_ONLY = {
        "scenario": "a customer calling to book a table",
        "termination_criteria": "",
        "expected_includes": [
            "# Scenario",
            "a customer calling to book a table",
            "Keep your responses natural and conversational",
        ],
        "expected_excludes": [
            "end_simulation",
            "conversation is considered complete",
        ],
    }

    TEST_CASE_WITH_TERMINATION = {
        "scenario": "a customer with a complaint",
        "termination_criteria": "The issue is resolved by the support agent.",
        "expected_includes": [
            "# Scenario",
            "a customer with a complaint",
            "The issue is resolved by the support agent.",
            "end_simulation",
            "conversation is considered complete when",
        ],
        "expected_excludes": [],
    }

    TEST_CASE_CUSTOM_TEMPLATE = {
        "scenario": "a technical support agent",
        "termination_criteria": "When done, call end_simulation.",
        "template": "Scenario: {scenario}\nGoal: {termination_criteria}",
        "expected_exact": "Scenario: a technical support agent\nGoal: When done, call end_simulation.",
    }

    # Create mock services
    stt = MockSTTService()
    llm = MockLLMService()
    tts = MockTTSService()

    # Test scenario only (no termination criteria)
    config1 = VoicegroundSimulatorConfig(
        llm=llm,
        tts=tts,
        stt=stt,
        scenario=str(TEST_CASE_SCENARIO_ONLY["scenario"]),
    )

    for expected in TEST_CASE_SCENARIO_ONLY["expected_includes"]:
        assert expected in config1.system_prompt, f"Expected '{expected}' in system prompt"

    for excluded in TEST_CASE_SCENARIO_ONLY["expected_excludes"]:
        assert excluded not in config1.system_prompt, f"Expected '{excluded}' NOT in system prompt"

    # Test with scenario and termination criteria
    config2 = VoicegroundSimulatorConfig(
        llm=llm,
        tts=tts,
        stt=stt,
        scenario=str(TEST_CASE_WITH_TERMINATION["scenario"]),
        termination_criteria=str(TEST_CASE_WITH_TERMINATION["termination_criteria"]),
    )

    for expected in TEST_CASE_WITH_TERMINATION["expected_includes"]:
        assert expected in config2.system_prompt, f"Expected '{expected}' in system prompt"

    # Test with custom template
    config3 = VoicegroundSimulatorConfig(
        llm=llm,
        tts=tts,
        stt=stt,
        scenario=str(TEST_CASE_CUSTOM_TEMPLATE["scenario"]),
        termination_criteria=str(TEST_CASE_CUSTOM_TEMPLATE["termination_criteria"]),
        system_prompt_template=str(TEST_CASE_CUSTOM_TEMPLATE["template"]),
    )

    assert config3.system_prompt == TEST_CASE_CUSTOM_TEMPLATE["expected_exact"]


def test_text_only_simulation_creation():
    """Test that text-only simulation can be created without STT/TTS."""

    # Create mock LLM service
    llm = MockLLMService(responses=[])
    observer = VoicegroundObserver()

    # Create configuration for text-only mode (no STT/TTS)
    config = VoicegroundSimulatorConfig(
        llm=llm,
        tts=None,
        stt=None,
        scenario="a test user in text mode",
        use_voice=False,  # Text-only mode
        observers=[observer],
    )

    # Create simulation instance
    simulation = VoicegroundSimulation(config)

    # Verify simulation has a transport
    assert simulation.transport is not None
    assert hasattr(simulation.transport, "input")
    assert hasattr(simulation.transport, "output")

    # Verify config is stored
    assert simulation._config == config
    assert simulation._config.use_voice is False


def test_voice_mode_requires_stt_tts():
    """Test that voice mode requires STT and TTS services."""

    llm = MockLLMService(responses=[])

    # Test that missing TTS raises ValueError
    with pytest.raises(ValueError, match="tts service is required when use_voice is True"):
        VoicegroundSimulatorConfig(
            llm=llm,
            tts=None,
            stt=MockSTTService(),
            scenario="test",
            use_voice=True,
        )

    # Test that missing STT raises ValueError
    with pytest.raises(ValueError, match="stt service is required when use_voice is True"):
        VoicegroundSimulatorConfig(
            llm=llm,
            tts=MockTTSService(),
            stt=None,
            scenario="test",
            use_voice=True,
        )

    # Test that both missing raises ValueError
    with pytest.raises(ValueError, match="tts service is required when use_voice is True"):
        VoicegroundSimulatorConfig(
            llm=llm,
            tts=None,
            stt=None,
            scenario="test",
            use_voice=True,
        )


@pytest.mark.asyncio
async def test_text_only_simulation_conversation():
    """Test a complete text-only simulation with 1 turn conversation."""

    # Expected conversation flow
    EXPECTED_CONVERSATION = [
        {"role": "user", "content": "Hello, how are you doing?"},
        {"role": "bot", "content": "Hey, I'm doing great how are you?"},
    ]

    # Extract responses for simulator (user) and bot
    user_responses = [msg["content"] for msg in EXPECTED_CONVERSATION if msg["role"] == "user"]
    bot_responses = [msg["content"] for msg in EXPECTED_CONVERSATION if msg["role"] == "bot"]

    # Create mock LLM for simulator
    simulator_llm = MockLLMService(responses=user_responses)

    summary_reporter = SummaryReporter()
    observer = VoicegroundObserver(reporters=[summary_reporter])

    # Configure text-only simulation
    simulator_config = VoicegroundSimulatorConfig(
        llm=simulator_llm,
        scenario="You are a user greeting a bot.",
        use_voice=False,
        initiate_conversation=True,  # Simulator (user) speaks first
        max_turns=1,
        timeout_seconds=10,
        observers=[observer],
    )

    # Run simulation with bot
    async with VoicegroundSimulation(simulator_config) as simulation:
        await run_mock_bot(
            transport=simulation.transport,
            responses=bot_responses,
            system_prompt="You are a friendly assistant.",
        )

    # Verify results from SummaryReporter
    assert len(summary_reporter.transcript_collector.entries) == len(EXPECTED_CONVERSATION)

    # Verify conversation order and content
    for i, expected_msg in enumerate(EXPECTED_CONVERSATION):
        actual_entry = summary_reporter.transcript_collector.entries[i]
        assert actual_entry.role == expected_msg["role"], (
            f"Expected role '{expected_msg['role']}' at position {i}, got '{actual_entry.role}'"
        )
        assert actual_entry.text == expected_msg["content"], (
            f"Expected text '{expected_msg['content']}' at position {i}, got '{actual_entry.text}'"
        )


@pytest.mark.asyncio
async def test_evaluation_system():
    """Test the complete evaluation system: configuration, execution, and results."""

    # Create a mock evaluator that returns a JSON response
    mock_evaluator = MockEvaluator(
        response='{"passed": true, "reasoning": "The bot successfully greeted the user"}'
    )

    # Create evaluation definitions
    evaluation1 = BooleanEvaluationDefinition(
        name="politeness",
        criteria="Was the bot polite and friendly?",
        evaluator=mock_evaluator,
    )

    evaluation2 = BooleanEvaluationDefinition(
        name="responsiveness",
        criteria="Did the bot respond appropriately to user messages?",
        evaluator=mock_evaluator,
    )

    # Test 1: VoicegroundEvaluator class with transcript including tool calls
    evaluator_instance = VoicegroundEvaluator(
        evaluations=[evaluation1, evaluation2],
        default_evaluator=mock_evaluator,
    )

    # Sample transcript with user, bot, and tool call
    transcript: list[dict] = [
        {"role": "user", "content": "Hello, what's the weather?"},
        {
            "role": "tool_call",
            "name": "get_weather",
            "arguments": {"location": "San Francisco"},
            "result": {"temperature": 72, "condition": "sunny"},
        },
        {"role": "bot", "content": "It's 72°F and sunny in San Francisco."},
    ]

    # Run evaluations
    results = await evaluator_instance.evaluate_conversation(transcript)

    # Verify evaluation results
    assert len(results) == 2
    assert results[0].name == "politeness"
    assert results[0].type == EvaluationType.BOOLEAN
    assert results[0].passed is True
    assert "successfully greeted" in results[0].reasoning
    assert results[1].name == "responsiveness"

    # Test 2: Observer integration
    observer = VoicegroundObserver(
        reporters=[],
        evaluations=[evaluation1],
        default_evaluator=mock_evaluator,
    )

    # Verify evaluator is configured in observer
    assert observer._evaluator is not None
    assert observer._evaluator._evaluations == [evaluation1]
    assert observer._evaluator._default_evaluator == mock_evaluator
