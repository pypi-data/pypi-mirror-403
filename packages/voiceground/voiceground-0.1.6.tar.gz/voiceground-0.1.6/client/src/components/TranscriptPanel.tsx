import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { VoicegroundEvent } from '@/types';

interface TranscriptEntry {
  role: 'user' | 'bot';
  text: string;
  timestamp: number;
}

interface TranscriptPanelProps {
  events: VoicegroundEvent[];
}

function extractTranscript(events: VoicegroundEvent[]): TranscriptEntry[] {
  const transcript: TranscriptEntry[] = [];
  
  // First pass: collect all TTS end event timestamps (to detect which LLM events have corresponding TTS)
  const ttsEndTimestamps = new Set<number>();
  const ttsStartToEndMap = new Map<number, number>(); // Map TTS start time to end time
  
  // Build a map of TTS start -> end times
  const ttsStarts = new Map<string, number>(); // category+source -> start timestamp
  for (const event of events) {
    if (event.category === 'tts' && event.type === 'start') {
      const key = `${event.category}-${event.source}`;
      ttsStarts.set(key, event.timestamp);
    } else if (event.category === 'tts' && event.type === 'end') {
      const key = `${event.category}-${event.source}`;
      const startTime = ttsStarts.get(key);
      if (startTime !== undefined) {
        ttsStartToEndMap.set(startTime, event.timestamp);
        ttsStarts.delete(key);
      }
      if (event.data.text) {
        ttsEndTimestamps.add(event.timestamp);
      }
    }
  }
  
  // Second pass: extract transcriptions
  for (const event of events) {
    // STT end events contain user transcriptions
    if (event.category === 'stt' && event.type === 'end' && event.data.text) {
      transcript.push({
        role: 'user',
        text: event.data.text,
        timestamp: event.timestamp,
      });
    }
    
    // TTS end events contain bot responses (what was actually spoken by TTS)
    // TTSTextFrame represents the actual spoken text returned by the TTS provider
    if (event.category === 'tts' && event.type === 'end' && event.data.text) {
      transcript.push({
        role: 'bot',
        text: event.data.text,
        timestamp: event.timestamp,
      });
    } 
    // Fallback: Use LLM end events only if there's no TTS end event nearby (within 5 seconds)
    else if (event.category === 'llm' && event.type === 'end' && event.data.text) {
      // Check if there's a TTS end event within 5 seconds after this LLM event
      const hasTTSNearby = Array.from(ttsEndTimestamps).some(
        ttsTime => ttsTime > event.timestamp && ttsTime - event.timestamp < 5
      );
      
      if (!hasTTSNearby) {
        transcript.push({
          role: 'bot',
          text: event.data.text,
          timestamp: event.timestamp,
        });
      }
    }
  }
  
  // Sort by timestamp
  return transcript.sort((a, b) => a.timestamp - b.timestamp);
}

export function TranscriptPanel({ events }: TranscriptPanelProps) {
  const transcript = useMemo(() => extractTranscript(events), [events]);
  
  if (transcript.length === 0) {
    return (
      <Card className="h-full border-border/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">Transcript</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground text-sm">
            No transcript available
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card className="h-full border-border/50 flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0">
        <CardTitle className="text-base font-semibold">
          Transcript
          <span className="text-xs text-muted-foreground font-normal ml-2">
            ({transcript.length} {transcript.length === 1 ? 'message' : 'messages'})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 min-h-0 px-0">
        <ScrollArea className="h-full px-6">
          <div className="space-y-4 pb-4">
            {transcript.map((entry, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${
                  entry.role === 'user' ? 'justify-start' : 'justify-start'
                }`}
              >
                <div className={`flex-shrink-0 w-16 text-xs font-medium pt-1 ${
                  entry.role === 'user' 
                    ? 'text-blue-400' 
                    : 'text-green-400'
                }`}>
                  {entry.role.toUpperCase()}
                </div>
                <div className={`flex-1 rounded-lg px-3 py-2 text-sm ${
                  entry.role === 'user'
                    ? 'bg-blue-500/10 border border-blue-500/20'
                    : 'bg-green-500/10 border border-green-500/20'
                }`}>
                  <p className="leading-relaxed whitespace-pre-wrap break-words">
                    {entry.text}
                  </p>
                  <div className="text-xs text-muted-foreground mt-1">
                    {new Date(entry.timestamp * 1000).toLocaleTimeString('en-US', {
                      hour12: false,
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      fractionalSecondDigits: 3,
                    })}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
