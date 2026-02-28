import { useState, useEffect, useCallback } from "react";
import { ProductInput } from "./components/ProductInput";
import { ActivityFeed } from "./components/ActivityFeed";
import { LeadsTable } from "./components/LeadsTable";
import { StrategyPanel } from "./components/StrategyPanel";
import { GraphVisualization } from "./components/GraphVisualization";
import { StrategyTimeline } from "./components/StrategyTimeline";
import { ResetButton } from "./components/ResetButton";
import { useActivityFeed } from "./hooks/useActivityFeed";

const REFRESH_EVENT_TYPES = [
  "strategy_stored",
  "market_research_done",
  "pivot_email_drafted",
  "outage_reprioritized",
  "graph_reset",
  "validation_complete",
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
    <div className="min-h-screen bg-surface text-text-primary dot-grid">
      {/* Accent glow behind header */}
      <div className="hero-glow">
        <header className="border-b border-border-subtle backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-6 pt-6 pb-5">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <img src="/recurve_icon.png" alt="Recurve AI" className="w-9 h-9 rounded-xl shadow-lg shadow-accent/20" />
                <div>
                  <h1 className="text-lg font-semibold tracking-tight text-text-primary">
                    Recurve AI
                  </h1>
                  <p className="text-[11px] text-text-tertiary -mt-0.5">AI-powered lead intelligence</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 text-xs text-text-tertiary bg-surface-overlay/50 px-3 py-1.5 rounded-full border border-border-subtle">
                  <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-success animate-pulse" : "bg-text-tertiary"}`} />
                  {connected ? "Live" : "Offline"}
                </div>
                <ResetButton onReset={bumpRefresh} />
              </div>
            </div>
            <ProductInput />
          </div>
        </header>
      </div>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
          <div className="lg:col-span-3 space-y-6">
            <Card title="Current Strategy" icon="strategy">
              <StrategyPanel refreshTrigger={refreshTrigger} />
            </Card>
            <Card title="Target Leads" icon="leads">
              <LeadsTable refreshTrigger={refreshTrigger} />
            </Card>
          </div>
          <div className="lg:col-span-2 space-y-6">
            <Card title="Live Activity" icon="activity" className="max-h-[460px] flex flex-col">
              <ActivityFeed events={events} />
            </Card>
            <Card title="Strategy Evolution" icon="timeline">
              <StrategyTimeline refreshTrigger={refreshTrigger} />
            </Card>
          </div>
        </div>

        <Card title="Knowledge Graph" icon="graph">
          <GraphVisualization refreshTrigger={refreshTrigger} />
        </Card>
      </main>
    </div>
  );
}

const CARD_ICONS: Record<string, React.ReactNode> = {
  strategy: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  leads: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  activity: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  timeline: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  graph: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
    </svg>
  ),
};

function Card({
  title,
  icon,
  children,
  className = "",
}: {
  title: string;
  icon?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`bg-surface-raised/80 backdrop-blur-sm rounded-xl border border-border-subtle overflow-hidden ${className}`}
    >
      <div className="px-5 py-3.5 border-b border-border-subtle flex items-center gap-2">
        {icon && CARD_ICONS[icon] && (
          <span className="text-text-tertiary">{CARD_ICONS[icon]}</span>
        )}
        <h3 className="text-sm font-medium text-text-secondary">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

export default App;
