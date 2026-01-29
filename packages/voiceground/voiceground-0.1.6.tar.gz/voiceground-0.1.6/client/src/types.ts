export type EventCategory = 'user_speak' | 'bot_speak' | 'stt' | 'llm' | 'tts' | 'tool_call' | 'system';
export type EventType = 'start' | 'end' | 'first_byte';

export interface VoicegroundEvent {
  id: string;
  timestamp: number;
  category: EventCategory;
  type: EventType;
  source: string;
  data: Record<string, unknown>;
}

export interface Turn {
  id: number;
  startTime: number;
  endTime: number;
  events: VoicegroundEvent[];
  metrics: TurnMetrics;
}

export interface TurnMetrics {
  /** Turn Duration: first event → last event in the turn */
  turnDuration: number;
  /** Response Time: user_speak:end → bot_speak:start */
  responseTime: number | null;
  /** Transcription Overhead: user_speak:end → stt:end */
  transcriptionOverhead: number | null;
  /** Voice Synthesis Overhead: tts:start → bot_speak:start */
  voiceSynthesisOverhead: number | null;
  /** LLM Response Time: llm:start → llm:first_byte */
  llmResponseTime: number | null;
  /** System Overhead: stt:end → llm:start (system category) */
  systemOverhead: number | null;
  /** Tools Overhead: sum of tool_call durations between llm:start and llm:end */
  toolsOverhead: number | null;
}

export type EvaluationType = 'boolean' | 'category' | 'rating';

export interface Evaluation {
  name: string;
  type: EvaluationType;
  passed?: boolean | null;
  category?: string | null;
  rating?: number | null;
  reasoning: string;
}

declare global {
  interface Window {
    __VOICEGROUND_EVENTS__?: VoicegroundEvent[];
    __VOICEGROUND_CONVERSATION_ID__?: string;
    __VOICEGROUND_VERSION__?: string;
    __VOICEGROUND_EVALUATIONS__?: Evaluation[];
  }
}

