# Voiceground

Observability framework for [Pipecat](https://github.com/pipecat-ai/pipecat) voice and multimodal conversational AI.

## Features

- **[Call Simulation](#call-simulation)**: Test your bots with dynamic, LLM-powered simulated users
- **[VoicegroundObserver](#voicegroundobserver)**: Track conversation events following Pipecat's Observer pattern
- **[Evaluations](#llm-as-a-judge-evaluations)**: Automatically assess conversation quality using LLMs

## Installation

```bash
pip install voiceground
```

Or with UV:

```bash
uv add voiceground
```

## Call Simulation

Voiceground includes a call simulation feature for testing your bots with dynamic, LLM-powered simulated users. Instead of manual testing, you can define user personas and goals, and let the simulator have realistic conversations with your bot.

![Voiceground Simulation](assets/VoicegroundSimulation.gif)

### Quick Start

```python
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.services.openai.tts import OpenAITTSService
from voiceground import HTMLReporter, VoicegroundObserver
from voiceground.simulation import VoicegroundSimulation, VoicegroundSimulatorConfig
from voiceground.evaluations import OpenAIEvaluator, BooleanEvaluationDefinition

# Create observer with HTML reporter and optional evaluations
html_reporter = HTMLReporter(output_dir="reports", auto_open=True)
evaluator = OpenAIEvaluator(api_key=openai_key, model="gpt-4o-mini")
observer = VoicegroundObserver(
    reporters=[html_reporter],
    evaluations=[
        BooleanEvaluationDefinition(
            name="goal_achievement",
            criteria="Did the bot successfully help the user achieve their goal?",
        )
    ],
    default_evaluator=evaluator,
)

# Configure the simulated user
config = VoicegroundSimulatorConfig(
    llm=OpenAILLMService(api_key=openai_key, model="gpt-4o-mini"),
    tts=OpenAITTSService(api_key=openai_key, voice="echo"),
    stt=OpenAISTTService(api_key=openai_key),
    scenario="You are a customer calling to book a restaurant table for 2 people tomorrow at 7pm.",
    termination_criteria="The reservation is confirmed by the resturant.",
    initiate_conversation=True,  # Simulator speaks first
    max_turns=5,
    timeout_seconds=60,
    observers=[observer],  # Observers automatically attached to bot
)

# Run simulation
async with VoicegroundSimulation(config) as simulation:
    await run_bot(transport=simulation.transport)
```

Your `run_bot` function just needs to accept a transport parameter, as a drop in replacement:

```python
async def run_bot(transport):
    # Use transport.input() and transport.output() - same as LocalAudioTransport!
    pipeline = Pipeline([
        transport.input(),
        stt, llm, tts,
        transport.output(),
    ])
    runner = PipelineRunner()
    await runner.run(PipelineTask(pipeline))
```

The simulation automatically handles turn limiting and timeouts - no extra configuration needed on the bot side.

**Note**: Simulations run faster than real-time because audio input/output is not buffered. This allows for rapid testing and iteration, but timing metrics may not reflect real-world performance characteristics.

### Architecture

```
┌───────────────────────────┐          ┌───────────────────────────┐
│   Simulator Pipeline      │          │     Bot Pipeline          │
│   (The "Fake User")       │          │   (Your actual bot)       │
│                           │          │                           │
│   STT ◄───────────────────┼── audio ─┼─── TTS                    │
│    ↓                      │          │     ↑                     │
│   LLM (user persona)      │          │    LLM                    │
│    ↓                      │          │     ↑                     │
│   TTS ────────────────────┼── audio ─┼──► STT                    │
│                           │          │                           │
└───────────────────────────┘          └───────────────────────────┘
                  VoicegroundBridgeTransport
```

Both pipelines are standard Pipecat pipelines connected via `VoicegroundBridgeTransport`. The simulator's LLM has a system prompt that tells it to act as a user with specific goals.

### Text-Only Simulation

Voiceground also supports text-only simulations for testing LLM-to-LLM conversations without speech synthesis or transcription:

```python
# Configure text-only simulation (no STT/TTS required)
config = VoicegroundSimulatorConfig(
    llm=OpenAILLMService(api_key=openai_key, model="gpt-4o-mini"),
    scenario="You are a customer with a technical issue.",
    use_voice=False,  # Enable text-only mode
    initiate_conversation=True,
    max_turns=5,
)

# Run simulation - works with text-based bots
async with VoicegroundSimulation(config) as simulation:
    await run_text_bot(transport=simulation.transport)
```

In text-only mode:
- The simulator LLM's text output goes directly to the bot (no TTS)
- The bot's text output goes directly to the simulator (no STT)
- The transport automatically configures LLMs to skip TTS by sending `LLMConfigureOutputFrame(skip_tts=True)`
- Transcription and voice synthesis events are not tracked

### VoicegroundSimulatorConfig Options

| Option | Type | Description |
|--------|------|-------------|
| `llm` | `LLMService` | LLM for generating user responses |
| `tts` | `Optional[TTSService]` | TTS for generating user voice (required if `use_voice=True`) |
| `stt` | `Optional[STTService]` | STT for transcribing bot speech (required if `use_voice=True`) |
| `scenario` | `str` | Description of the simulation scenario |
| `use_voice` | `bool` | If True, uses audio with STT/TTS. If False, text-only simulation (default: True) |
| `termination_criteria` | `str` | When the simulation should end (optional) |
| `system_prompt_template` | `str` | Template for building system prompt (default provided) |
| `initiate_conversation` | `bool` | If True, simulator speaks first (default: False) |
| `max_turns` | `int` | Maximum conversation turns (default: 10) |
| `timeout_seconds` | `float` | Maximum simulation duration (default: 120) |
| `observers` | `list[BaseObserver]` | Observers to attach to bot pipeline (default: []) |


### Accessing Results

To collect simulation data (transcript, events, evaluations), use a `SummaryReporter`:

```python
from voiceground import SummaryReporter

# Create reporter to collect data
summary_reporter = SummaryReporter()
observer = VoicegroundObserver(reporters=[summary_reporter])

# After simulation
print(f"Transcript: {len(summary_reporter.transcript_collector.entries)} messages")
print(f"Events: {len(summary_reporter.events)} events")
print(f"Evaluations: {len(summary_reporter.evaluations)} results")
```

## VoicegroundObserver

Track conversation events following Pipecat's Observer pattern for observability and debugging.

![Voiceground Observer](assets/VoicegroundObserver.gif)

### Quick Start

```python
import uuid
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from voiceground import VoicegroundObserver, HTMLReporter
from voiceground.evaluations import OpenAIEvaluator, BooleanEvaluationDefinition

# Create observer with HTML reporter and optional evaluations
conversation_id = str(uuid.uuid4())
reporter = HTMLReporter(output_dir="reports")
evaluator = OpenAIEvaluator(api_key="your-openai-key", model="gpt-4o-mini")
observer = VoicegroundObserver(
    reporters=[reporter],
    conversation_id=conversation_id,
    evaluations=[
        BooleanEvaluationDefinition(
            name="conversation_quality",
            criteria="Was the conversation natural and helpful?",
        )
    ],
    default_evaluator=evaluator,
)

# Create pipeline task with observer
task = PipelineTask(
    pipeline=Pipeline([...]),
    observers=[observer]
)

# Run your pipeline
```

## LLM-as-a-Judge Evaluations

Voiceground includes a powerful evaluation system that uses LLMs to assess conversation quality automatically. Evaluations run after conversations end with the full transcript (user messages, bot responses, and tool calls) and results are included in HTML reports.

![Voiceground Evaluations](assets/VoicegroundEvaluations.png)

### Overview

The evaluation system allows you to:
- Define custom evaluation criteria in natural language
- Use LLMs to judge conversation quality automatically
- Support multiple evaluation types (boolean pass/fail, categories, ratings)
- Review results in interactive HTML reports
- Access evaluation results programmatically

### Quick Example

```python
from voiceground import VoicegroundObserver, HTMLReporter
from voiceground.evaluations import OpenAIEvaluator, BooleanEvaluationDefinition

# Create an evaluator
evaluator = OpenAIEvaluator(
    api_key="your-openai-key",
    model="gpt-4o-mini",  # Use models that support structured outputs
    temperature=0.0
)

# Define evaluation criteria
evaluations = [
    BooleanEvaluationDefinition(
        name="goal_achievement",
        criteria="Did the bot successfully help the user achieve their goal?",
    ),
    BooleanEvaluationDefinition(
        name="conversation_naturalness",
        criteria="Was the conversation natural and engaging?",
    ),
]

# Create observer with evaluations
html_reporter = HTMLReporter(output_dir="reports", auto_open=True)
observer = VoicegroundObserver(
    reporters=[html_reporter],
    evaluations=evaluations,
    default_evaluator=evaluator,  # Used when evaluation doesn't specify one
)

# Use in simulation or regular pipeline
config = VoicegroundSimulatorConfig(
    llm=...,
    scenario="You are a customer calling to book a table",
    observers=[observer],
)

async with VoicegroundSimulation(config) as simulation:
    await run_bot(simulation.transport)

# Access evaluation results from SummaryReporter
for result in summary_reporter.evaluations:
    print(f"{result.name}: {'✓ Passed' if result.passed else '✗ Failed'}")
    print(f"Reasoning: {result.reasoning}")
```

### Evaluation Types

Voiceground supports three evaluation types:

#### Boolean (Pass/Fail)
```python
BooleanEvaluationDefinition(
    name="goal_achievement",
    criteria="Did the bot successfully complete the task?",
)
```

#### Category Classification
```python
CategoryEvaluationDefinition(
    name="conversation_tone",
    criteria="Classify the tone of the conversation",
    categories=["professional", "friendly", "frustrated", "confused"],
)
```

#### Rating
```python
RatingEvaluationDefinition(
    name="response_quality",
    criteria="Rate the quality of the bot's responses",
    min_rating=1,
    max_rating=5,
)
```

### What Gets Evaluated

Evaluations receive the complete conversation context:
- **User messages**: All user inputs during the conversation
- **Bot responses**: All bot outputs including reasoning
- **Tool calls**: Function calls made by the LLM and their results
- **Timestamps**: Full conversation timeline

This allows evaluations to measure:
- Goal achievement (did the bot complete the task?)
- Conversation quality (natural, helpful, engaging?)
- Tool usage accuracy (were the right functions called?)
- Error handling (how did the bot handle issues?)

### Evaluator

Voiceground uses OpenAI's API for LLM-as-a-judge evaluations:

```python
evaluator = OpenAIEvaluator(
    api_key="your-openai-key",
    model="gpt-4o-mini",  # or "gpt-4o", etc.
    temperature=0.0
)
```

You can specify a different evaluator for each evaluation definition, or set a default evaluator when creating the observer:

```python
observer = VoicegroundObserver(
    reporters=[html_reporter],
    evaluations=[...],
    default_evaluator=evaluator,  # Used when evaluation doesn't specify one
)

### Viewing Results

Evaluation results appear in multiple places:

#### 1. HTML Report
The HTML report includes an "Evaluations" tab showing:
- Summary cards (total, passed, failed)
- Detailed table with results and reasoning
- Visual indicators (✓ for passed, ✗ for failed)

#### 2. Programmatic Access
```python
# After simulation - access from SummaryReporter
for result in summary_reporter.evaluations:
    print(f"Name: {result.name}")
    print(f"Type: {result.type}")
    print(f"Passed: {result.passed}")
    print(f"Reasoning: {result.reasoning}")
```

#### 3. EvaluationResult Model
```python
class EvaluationResult(BaseModel):
    name: str
    type: EvaluationType
    passed: bool | None = None      # For BOOLEAN
    category: str | None = None     # For CATEGORY
    rating: int | None = None       # For RATING (future)
    reasoning: str                  # LLM's explanation
```

## Tested With

Voiceground has been tested with the following Pipecat providers:

### LLM Providers
- [x] OpenAI

### STT Providers
- [x] ElevenLabs
- [x] OpenAI

### TTS Providers
- [x] ElevenLabs
- [x] OpenAI

## Event Categories

Voiceground tracks the following event categories:

| Category | Types | Description |
|----------|-------|-------------|
| `user_speak` | `start`, `end` | User speech events |
| `bot_speak` | `start`, `end` | Bot speech events |
| `stt` | `start`, `end` | Speech-to-text processing (includes transcription text) |
| `llm` | `start`, `first_byte`, `end` | LLM response generation (includes generated text) |
| `tts` | `start`, `first_byte`, `end` | Text-to-speech synthesis |
| `tool_call` | `start`, `end` | LLM function/tool calling |
| `system` | `start`, `end` | System events (e.g., context aggregation) |

## Opinionated Metrics

Voiceground tracks 7 opinionated metrics per conversation turn, providing comprehensive insights into voice conversation performance:

1. **Turn Duration**: Total time from the first event to the last event in the turn (milliseconds). Measures the complete duration of a conversation turn.

2. **Response Time**: Time from `user_speak:end` to `bot_speak:start` (or from the first event to `bot_speak:start` if the conversation started with bot speech). This is the end-to-end time the user experiences waiting for a response.

3. **Transcription Overhead**: Time from `user_speak:end` to `stt:end` (milliseconds). Measures the latency of speech-to-text processing.

4. **Voice Synthesis Overhead**: Time from `tts:start` to `bot_speak:start` (milliseconds). Measures the latency of text-to-speech synthesis.

5. **LLM Response Time**: Time from `llm:start` to `llm:first_byte` (milliseconds). Measures the time-to-first-byte for the LLM response, indicating how quickly the model starts generating content.

6. **System Overhead**: Time from `stt:end` to `llm:start` (milliseconds). Measures context aggregation and other system processing that occurs between transcription and LLM invocation. Includes labels/metadata about the system operations.

7. **Tools Overhead**: Sum of all individual `tool_call` durations (each `tool_call:end - tool_call:start`) that occur between `llm:start` and `llm:end` (milliseconds). Measures the total time spent executing function/tool calls during LLM processing.

### Metric Relationships

The metrics are related as follows:
- **Response Time** ≈ **Transcription Overhead** + **System Overhead** + **LLM Response Time** + **Tools Overhead** + **Voice Synthesis Overhead**
- **Turn Duration** includes all events in the turn and may be longer than Response Time if there are additional events before or after the main response flow

## Report Features

The generated HTML reports include:

- **Timeline Visualization**: Interactive timeline showing all events and their relationships
- **Events Table**: Detailed view of all tracked events with timestamps, sources, and data
- **Turns Table**: Conversation turns with all 7 opinionated performance metrics
- **Metrics Summary**: Average metrics across the conversation
- **Event Highlighting**: Hover over events or turns to see related events highlighted


## Examples

See the `examples/` directory for complete working examples:

### Bot Implementations

- **bots/restaurant_bot.py**: Restaurant booking assistant bot
- **bots/friendly_assistant_bot.py**: General-purpose friendly assistant bot

Both bots accept STT, LLM, and TTS services as parameters for flexibility.

### Runner Scripts

- **simulations/run_openai_simulation.py**: Call simulation with a restaurant booking scenario using OpenAI
- **observer/run_openai_restaurant_bot_with_observer.py**: Restaurant bot with OpenAI services (STT, LLM, TTS)
- **observer/run_elevenlabs_restaurant_bot_with_observer.py**: Restaurant bot with ElevenLabs (STT, TTS) and OpenAI (LLM)

To run an example:

```bash
# Install example dependencies
uv sync --all-extras

# Set required environment variables
export OPENAI_API_KEY=your_key
export ELEVENLABS_API_KEY=your_key  # For ElevenLabs examples

# Run a simulation (recommended first step)
python examples/simulations/run_openai_simulation.py

# Run a restaurant bot example
python examples/observer/run_openai_restaurant_bot_with_observer.py
# or
python examples/observer/run_elevenlabs_restaurant_bot_with_observer.py
```

**Note**: On macOS, you'll need to install portaudio for audio support:
```bash
brew install portaudio
```

## Development

```bash
# Clone the repository
git clone https://github.com/poseneror/voiceground.git
cd voiceground

# Install all dependencies (including dev and examples)
uv sync --all-extras

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy src

# Build the client
python scripts/develop.py build

# Run example (requires portaudio on macOS: brew install portaudio)
python scripts/develop.py example
```

## License

BSD-2-Clause License - see [LICENSE](LICENSE) for details.

