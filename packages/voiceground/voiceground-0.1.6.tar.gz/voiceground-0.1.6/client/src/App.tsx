import { useMemo, useState } from 'react';
import { EventsTable } from '@/components/EventsTable';
import { TurnsTable } from '@/components/TurnsTable';
import { EvaluationsTable } from '@/components/EvaluationsTable';
import { TranscriptPanel } from '@/components/TranscriptPanel';
import { SessionTimeline } from '@/components/SessionTimeline';
import { AppHeader } from '@/components/AppHeader';
import { AppFooter } from '@/components/AppFooter';
import { EmptyState } from '@/components/EmptyState';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { parseTurns } from '@/components/TurnsView';
import { useEvents } from '@/hooks/useEvents';

type ViewMode = 'evaluations' | 'turns' | 'events';

function App() {
  const { events, isMockData } = useEvents();
  const evaluations = useMemo(() => window.__VOICEGROUND_EVALUATIONS__ || [], []);
  const [viewMode, setViewMode] = useState<ViewMode>(evaluations.length > 0 ? 'evaluations' : 'turns');

  const turns = useMemo(() => parseTurns(events), [events]);

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header - Fixed */}
      <AppHeader 
        turns={turns}
        isMockData={isMockData}
      />

      {/* Main Content - Takes remaining space between header and footer */}
      <div className="flex-1 overflow-hidden min-h-0 flex">
        {events.length === 0 ? (
          <main className="flex-1">
            <div className="h-full w-full max-w-[1600px] mx-auto px-8 py-4">
              <EmptyState />
            </div>
          </main>
        ) : (
          <>
            {/* Main Content Area: Tables and Timeline */}
            <main className="flex-1 overflow-hidden min-h-0">
              <div className="h-full w-full px-8 py-4 flex flex-col gap-4">
                {/* View Mode Tabs */}
                <Tabs value={viewMode} onValueChange={(value) => setViewMode(value as ViewMode)} className="flex-1 min-h-0 flex flex-col gap-0">
                  <div className="flex-shrink-0 pb-2">
                    <TabsList className="w-fit">
                      {evaluations.length > 0 && (
                        <TabsTrigger value="evaluations" className="px-4">Evaluations</TabsTrigger>
                      )}
                      <TabsTrigger value="turns" className="px-4">Per-Turn Breakdown</TabsTrigger>
                      <TabsTrigger value="events" className="px-4">Events Timeline</TabsTrigger>
                    </TabsList>
                  </div>

                  {/* Tables */}
                  <TabsContent value="evaluations" className="flex-1 min-h-0 mt-0 overflow-hidden">
                    <EvaluationsTable evaluations={evaluations} />
                  </TabsContent>
                  <TabsContent value="turns" className="flex-1 min-h-0 mt-0 overflow-hidden">
                    <TurnsTable turns={turns} />
                  </TabsContent>
                  <TabsContent value="events" className="flex-1 min-h-0 mt-0 overflow-hidden">
                    <EventsTable events={events} />
                  </TabsContent>
                </Tabs>

                {/* Session Timeline - Always Visible */}
                <div className="flex-shrink-0">
                  <h3 className="text-sm font-semibold mb-3">Session Timeline</h3>
                  <SessionTimeline events={events} />
                </div>
              </div>
            </main>

            {/* Right Sidebar: Transcript Panel - Full height, proportional width */}
            <aside className="w-[30vw] min-w-[350px] max-w-[600px] flex-shrink-0 border-l border-border bg-muted/30">
              <div className="h-full px-6 py-4">
                <TranscriptPanel events={events} />
              </div>
            </aside>
          </>
        )}
      </div>

      {/* Footer - Fixed */}
      <AppFooter turns={turns.length} />
    </div>
  );
}

export default App;
