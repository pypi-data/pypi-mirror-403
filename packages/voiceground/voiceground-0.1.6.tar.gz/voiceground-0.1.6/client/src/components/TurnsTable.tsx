import { useMemo, useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { highlightAtom, createSegmentHighlight } from '@/atoms';
import { formatDuration } from '@/components/SessionTimeline';
import { getCategoryConfig } from '@/config';
import { DataTable } from '@/components/DataTable';
import type { Turn, VoicegroundEvent } from '@/types';

function getMetricEventIds(turn: Turn, metric: string, toolName?: string): { startEventId: string; endEventId: string } | null {
  const findEvent = (category: string, type: string) =>
    turn.events.find((e) => e.category === category && e.type === type);
  
  const findAllEvents = (category: string, type: string) =>
    turn.events.filter((e) => e.category === category && e.type === type);

  const userSpeakEnd = findEvent('user_speak', 'end');
  const sttEnd = findEvent('stt', 'end');
  const llmFirstByte = findEvent('llm', 'first_byte');
  const ttsStart = findEvent('tts', 'start');
  const botSpeakStart = findEvent('bot_speak', 'start');

  // Use the first LLM start for metrics (even if there are multiple LLM calls)
  const llmStarts = findAllEvents('llm', 'start');
  const llmStart = llmStarts.length > 0
    ? llmStarts.sort((a, b) => a.timestamp - b.timestamp)[0]  // First LLM start
    : undefined;

  switch (metric) {
    case 'response':
      if (userSpeakEnd && botSpeakStart) {
        // Normal case: user spoke first
        return { startEventId: userSpeakEnd.id, endEventId: botSpeakStart.id };
      } else if (!userSpeakEnd && botSpeakStart) {
        // Conversation started with bot speech: from first event to bot speak start
        const firstEvent = turn.events.sort((a, b) => a.timestamp - b.timestamp)[0];
        if (firstEvent) {
          return { startEventId: firstEvent.id, endEventId: botSpeakStart.id };
        }
      }
      break;
    case 'transcription':
      if (userSpeakEnd && sttEnd) return { startEventId: userSpeakEnd.id, endEventId: sttEnd.id };
      break;
    case 'llmResponse':
      if (llmStart && llmFirstByte) return { startEventId: llmStart.id, endEventId: llmFirstByte.id };
      break;
    case 'voiceSynthesis':
      if (ttsStart && botSpeakStart) return { startEventId: ttsStart.id, endEventId: botSpeakStart.id };
      break;
    case 'system':
      if (sttEnd && llmStart) return { startEventId: sttEnd.id, endEventId: llmStart.id };
      break;
    case 'tools': {
      // For tools, we need to find the first tool_call start and last tool_call end within LLM phase
      const llmEnd = findEvent('llm', 'end');
      if (llmStart && llmEnd) {
        const toolCallStarts = findAllEvents('tool_call', 'start')
          .filter(e => e.timestamp >= llmStart!.timestamp && e.timestamp <= llmEnd!.timestamp)
          .sort((a, b) => a.timestamp - b.timestamp);
        const toolCallEnds = findAllEvents('tool_call', 'end')
          .filter(e => e.timestamp >= llmStart!.timestamp && e.timestamp <= llmEnd!.timestamp)
          .sort((a, b) => a.timestamp - b.timestamp);
        
        if (toolCallStarts.length > 0 && toolCallEnds.length > 0) {
          return { startEventId: toolCallStarts[0].id, endEventId: toolCallEnds[toolCallEnds.length - 1].id };
        }
      }
      break;
    }
    case 'tool': {
      // For individual tool, find the specific tool_call start and end
      if (toolName) {
        const llmEnd = findEvent('llm', 'end');
        if (llmStart && llmEnd) {
          const toolCallStart = findAllEvents('tool_call', 'start')
            .find(e => 
              e.timestamp >= llmStart!.timestamp && 
              e.timestamp <= llmEnd!.timestamp &&
              (e.data?.operation === toolName || e.data?.name === toolName)
            );
          
          if (toolCallStart) {
            const toolCallEnd = findAllEvents('tool_call', 'end')
              .find(e => 
                e.timestamp > toolCallStart.timestamp &&
                e.timestamp <= llmEnd!.timestamp &&
                (e.data?.operation === toolName || e.data?.name === toolName)
              );
            
            if (toolCallEnd) {
              return { startEventId: toolCallStart.id, endEventId: toolCallEnd.id };
            }
          }
        }
      }
      break;
    }
  }
  return null;
}

function getToolCalls(turn: Turn): Array<{ name: string; startEvent: VoicegroundEvent; endEvent: VoicegroundEvent; duration: number }> {
  const findAllEvents = (category: string, type: string) =>
    turn.events.filter((e) => e.category === category && e.type === type);

  // Find all LLM starts to determine the range where tool calls might occur
  const llmStarts = findAllEvents('llm', 'start')
    .sort((a, b) => a.timestamp - b.timestamp);
  const llmEnds = findAllEvents('llm', 'end')
    .sort((a, b) => a.timestamp - b.timestamp);

  if (llmStarts.length === 0) return [];

  // Tool calls can start during any LLM phase, and can end after the LLM phase
  // Find the first LLM start and the last LLM end to define the search range
  const firstLlmStart = llmStarts[0];
  const lastLlmEnd = llmEnds.length > 0 ? llmEnds[llmEnds.length - 1] : null;
  
  // Tool calls that start during any LLM phase (between first LLM start and last LLM end)
  const minTimestamp = firstLlmStart.timestamp;
  const maxTimestamp = lastLlmEnd ? lastLlmEnd.timestamp : Infinity;

  const toolCallStarts = findAllEvents('tool_call', 'start')
    .filter(e => e.timestamp >= minTimestamp && (lastLlmEnd ? e.timestamp <= maxTimestamp : true))
    .sort((a, b) => a.timestamp - b.timestamp);

  const toolCalls: Array<{ name: string; startEvent: VoicegroundEvent; endEvent: VoicegroundEvent; duration: number }> = [];
  const usedEndEvents = new Set<string>();

  for (const startEvent of toolCallStarts) {
    const toolName = (startEvent.data?.operation as string) || (startEvent.data?.name as string) || 'unknown_tool';
    
    // Find the matching end event - it can be after the LLM phase ends
    // Also handle cases where there might be multiple end events (take the first unused one)
    const endEvent = findAllEvents('tool_call', 'end')
      .filter(e => 
        !usedEndEvents.has(e.id) &&
        e.timestamp > startEvent.timestamp &&
        ((e.data?.operation === toolName) || (e.data?.name === toolName))
      )
      .sort((a, b) => a.timestamp - b.timestamp)[0];

    if (endEvent) {
      usedEndEvents.add(endEvent.id);
      const duration = (endEvent.timestamp - startEvent.timestamp) * 1000; // Convert to milliseconds
      toolCalls.push({ name: toolName, startEvent, endEvent, duration });
    }
  }

  return toolCalls;
}

export interface TurnsTableProps {
  turns: Turn[];
}

export function TurnsTable({ turns }: TurnsTableProps) {
  const setHighlight = useSetAtom(highlightAtom);

  const handleTurnHover = useCallback((turnIndex: number) => {
    const turn = turns[turnIndex];
    // Find the first and last events of the turn
    const sortedEvents = [...turn.events].sort((a, b) => a.timestamp - b.timestamp);
    if (sortedEvents.length >= 2) {
      const firstEvent = sortedEvents[0];
      const lastEvent = sortedEvents[sortedEvents.length - 1];
      setHighlight(createSegmentHighlight(firstEvent.id, lastEvent.id, turnIndex, 'turn'));
    }
  }, [turns, setHighlight]);

  const handleTurnLeave = useCallback(() => {
    setHighlight(null);
  }, [setHighlight]);

  const handleMetricHover = useCallback((turnIndex: number, metric: string, toolName?: string) => {
    const turn = turns[turnIndex];
    if (metric === 'tools' && !toolName) {
      // For tools hover, highlight all tool segments
      const toolCalls = getToolCalls(turn);
      if (toolCalls.length > 0) {
        // Create highlights for all tools - use the first tool's start and last tool's end
        const firstTool = toolCalls[0];
        const lastTool = toolCalls[toolCalls.length - 1];
        setHighlight(createSegmentHighlight(firstTool.startEvent.id, lastTool.endEvent.id, turnIndex, metric));
      }
    } else {
      const eventIds = getMetricEventIds(turn, metric, toolName);
      if (eventIds) {
        setHighlight(createSegmentHighlight(eventIds.startEventId, eventIds.endEventId, turnIndex, metric));
      }
    }
  }, [turns, setHighlight]);

  const handleMetricLeave = useCallback(() => {
    setHighlight(null);
  }, [setHighlight]);

  const columns = useMemo(() => [
    {
      header: 'Turn',
      cell: (_turn: Turn, index: number) => (
        <div
          className="w-full h-full flex items-center"
          onMouseEnter={(e) => {
            e.stopPropagation();
            handleTurnHover(index);
          }}
          onMouseLeave={(e) => {
            e.stopPropagation();
            handleTurnLeave();
          }}
        >
          <span className="font-medium">#{index + 1}</span>
        </div>
      ),
      className: 'w-[60px]',
      cellClassName: 'hover:bg-muted/50 transition-colors',
    },
    {
      header: 'Response',
      cell: (turn: Turn, index: number) => (
        <div
          className="w-full h-full flex items-center"
          onMouseEnter={(e) => {
            e.stopPropagation();
            handleMetricHover(index, 'response');
          }}
          onMouseLeave={(e) => {
            e.stopPropagation();
            handleMetricLeave();
          }}
        >
          <span className="text-primary font-semibold cursor-pointer">
            {formatDuration(turn.metrics.responseTime)}
          </span>
        </div>
      ),
      cellClassName: 'hover:bg-primary/10 transition-colors cursor-pointer',
    },
    {
      header: 'Transcription',
      cell: (turn: Turn, index: number) => (
        <div
          className="w-full h-full flex items-center"
          onMouseEnter={(e) => {
            e.stopPropagation();
            handleMetricHover(index, 'transcription');
          }}
          onMouseLeave={(e) => {
            e.stopPropagation();
            handleMetricLeave();
          }}
        >
          <span className={`${getCategoryConfig('stt').metricColor} cursor-pointer`}>
            {formatDuration(turn.metrics.transcriptionOverhead)}
          </span>
        </div>
      ),
      cellClassName: `${getCategoryConfig('stt').metricHoverColor} transition-colors cursor-pointer`,
    },
    {
      header: 'System',
      cell: (turn: Turn, index: number) => (
        <div
          className="w-full h-full flex items-center"
          onMouseEnter={(e) => {
            e.stopPropagation();
            handleMetricHover(index, 'system');
          }}
          onMouseLeave={(e) => {
            e.stopPropagation();
            handleMetricLeave();
          }}
        >
          <span className={`${getCategoryConfig('system').metricColor} cursor-pointer`}>
            {formatDuration(turn.metrics.systemOverhead)}
          </span>
        </div>
      ),
      cellClassName: `${getCategoryConfig('system').metricHoverColor} transition-colors cursor-pointer`,
    },
    {
      header: 'LLM Response',
      cell: (turn: Turn, index: number) => (
        <div
          className="w-full h-full flex items-center"
          onMouseEnter={(e) => {
            e.stopPropagation();
            handleMetricHover(index, 'llmResponse');
          }}
          onMouseLeave={(e) => {
            e.stopPropagation();
            handleMetricLeave();
          }}
        >
          <span className={`${getCategoryConfig('llm').metricColor} cursor-pointer`}>
            {formatDuration(turn.metrics.llmResponseTime)}
          </span>
        </div>
      ),
      cellClassName: `${getCategoryConfig('llm').metricHoverColor} transition-colors cursor-pointer`,
    },
    {
      header: 'Tools',
      cell: (turn: Turn, index: number) => {
        const toolCalls = getToolCalls(turn);
        
        if (toolCalls.length === 0) {
          return (
            <div className="w-full h-full flex items-center">
              <span className="text-muted-foreground">
                {formatDuration(turn.metrics.toolsOverhead)}
              </span>
            </div>
          );
        }

        const avgDuration = toolCalls.reduce((sum, tool) => sum + tool.duration, 0) / toolCalls.length;

        return (
          <div
            className="w-full h-full flex items-center"
            onMouseEnter={(e) => {
              e.stopPropagation();
              handleMetricHover(index, 'tools');
            }}
            onMouseLeave={(e) => {
              e.stopPropagation();
              handleMetricLeave();
            }}
          >
            <span className={`${getCategoryConfig('tool_call').metricColor} cursor-pointer`}>
              {formatDuration(avgDuration)}
            </span>
          </div>
        );
      },
      cellClassName: `${getCategoryConfig('tool_call').metricHoverColor} transition-colors cursor-pointer`,
    },
    {
      header: 'Voice Synthesis',
      cell: (turn: Turn, index: number) => (
        <div
          className="w-full h-full flex items-center"
          onMouseEnter={(e) => {
            e.stopPropagation();
            handleMetricHover(index, 'voiceSynthesis');
          }}
          onMouseLeave={(e) => {
            e.stopPropagation();
            handleMetricLeave();
          }}
        >
          <span className={`${getCategoryConfig('tts').metricColor} cursor-pointer`}>
            {formatDuration(turn.metrics.voiceSynthesisOverhead)}
          </span>
        </div>
      ),
      cellClassName: `${getCategoryConfig('tts').metricHoverColor} transition-colors cursor-pointer`,
    },
    {
      header: 'Turn Duration',
      cell: (turn: Turn, index: number) => (
        <div
          className="w-full h-full flex items-center justify-end"
          onMouseEnter={(e) => {
            e.stopPropagation();
            handleTurnHover(index);
          }}
          onMouseLeave={(e) => {
            e.stopPropagation();
            handleTurnLeave();
          }}
        >
          <span className="text-right text-muted-foreground">
            {formatDuration(turn.metrics.turnDuration)}
          </span>
        </div>
      ),
      className: 'text-right w-[100px]',
      cellClassName: 'hover:bg-muted/50 transition-colors',
    },
  ], [handleMetricHover, handleMetricLeave, handleTurnHover, handleTurnLeave]);

  if (turns.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <p className="font-medium mb-1">No turns recorded</p>
          <p className="text-xs">No conversation turns have been detected yet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col min-h-0 overflow-hidden">
      <DataTable
        columns={columns}
        data={turns}
        emptyMessage="No turns recorded"
        onRowMouseEnter={(_turn, index) => handleTurnHover(index)}
        onRowMouseLeave={() => handleTurnLeave()}
        rowClassName={() => 'cursor-pointer'}
        getRowKey={(turn) => turn.id}
      />
      <p className="text-xs text-muted-foreground mt-4 flex-shrink-0">
        Hover over metrics to highlight in timeline
      </p>
    </div>
  );
}

