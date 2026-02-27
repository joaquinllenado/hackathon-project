import { useState, useEffect, useCallback } from "react";
import { ProductInput } from "./components/ProductInput";
import { ActivityFeed } from "./components/ActivityFeed";
import { LeadsTable } from "./components/LeadsTable";
import { StrategyPanel } from "./components/StrategyPanel";
import { GraphVisualization } from "./components/GraphVisualization";
import { StrategyTimeline } from "./components/StrategyTimeline";
import { MockTriggerButton } from "./components/MockTriggerButton";
import { ResetButton } from "./components/ResetButton";
import { useActivityFeed } from "./hooks/useActivityFeed";

const REFRESH_EVENT_TYPES = [
  "strategy_stored",
  "market_research_done",
  "pivot_email_drafted",
  "mock_trigger_response",
  "graph_reset",
];

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const { events, connected } = useActivityFeed();

  const bumpRefresh = useCallback(() => {
    setRefreshTrigger((t) => t + 1);
  }, []);

  useEffect(() => {
    if (events.length === 0) return;
    const latest = events[0];
    if (REFRESH_EVENT_TYPES.includes(latest.type)) {
      setRefreshTrigger((t) => t + 1);
    }
  }, [events]);

  return (
    <div className="min-h-screen bg-surface text-text-primary">
      <header className="border-b border-border-subtle">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-purple-500 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h1 className="text-lg font-semibold tracking-tight text-text-primary">
                Recursive Hunter
              </h1>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 text-xs text-text-tertiary">
                <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-success" : "bg-text-tertiary"}`} />
                {connected ? "Connected" : "Offline"}
              </div>
              <ResetButton onReset={bumpRefresh} />
              <MockTriggerButton />
            </div>
          </div>
          <ProductInput />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
          <div className="lg:col-span-3 space-y-6">
            <Card title="Current Strategy">
              <StrategyPanel refreshTrigger={refreshTrigger} />
            </Card>
            <Card title="Target Leads">
              <LeadsTable refreshTrigger={refreshTrigger} />
            </Card>
          </div>
          <div className="lg:col-span-2 space-y-6">
            <Card title="Live Activity" className="max-h-[460px] flex flex-col">
              <ActivityFeed events={events} />
            </Card>
            <Card title="Strategy Evolution">
              <StrategyTimeline refreshTrigger={refreshTrigger} />
            </Card>
          </div>
        </div>

        <Card title="Knowledge Graph">
          <GraphVisualization refreshTrigger={refreshTrigger} />
        </Card>
      </main>
    </div>
  );
}

function Card({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`bg-surface-raised rounded-xl border border-border-subtle overflow-hidden ${className}`}
    >
      <div className="px-5 py-3.5 border-b border-border-subtle">
        <h3 className="text-sm font-medium text-text-secondary">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

export default App;
