/**
 * Centralized configuration for metrics display.
 */

export interface MetricConfig {
  /** Display label */
  label: string;
  /** Short label for compact display */
  shortLabel: string;
  /** Description of what this metric measures */
  description: string;
}

export const METRIC_CONFIG: Record<string, MetricConfig> = {
  responseTime: {
    label: 'Response',
    shortLabel: 'Response',
    description: 'Time from user speech end to bot speech start',
  },
  transcriptionOverhead: {
    label: 'Transcription',
    shortLabel: 'Transcription',
    description: 'Time from user activity end to the production of text (transcription overhead)',
  },
  systemOverhead: {
    label: 'System',
    shortLabel: 'System',
    description: 'Time from text production end to the start of the LLM processing (system overhead)',
  },
  llmResponseTime: {
    label: 'LLM Response',
    shortLabel: 'LLM Response',
    description: 'Time from the start of the LLM processing to the first byte of the response (LLM response time)',
  },
  toolsOverhead: {
    label: 'Tools',
    shortLabel: 'Tools',
    description: 'Sum of tool call durations during the LLM processing (tools overhead)',
  },
  voiceSynthesisOverhead: {
    label: 'Voice Synthesis',
    shortLabel: 'Voice Synthesis',
    description: 'Time from the start of the text-to-speech synthesis to the start of the bot speech (voice synthesis overhead)',
  },
  turnDuration: {
    label: 'Turn Duration',
    shortLabel: 'Turn Duration',
    description: 'Total time from the first event to the last event in the turn',
  },
};

/**
 * Get metric configuration
 */
export function getMetricConfig(metricKey: string): MetricConfig | undefined {
  return METRIC_CONFIG[metricKey];
}

/**
 * Get metric label
 */
export function getMetricLabel(metricKey: string): string {
  return METRIC_CONFIG[metricKey]?.label || metricKey;
}

