import type { ActivityEvent } from "../types/api";

const EVENT_CONFIG: Record<string, { label: string; icon: string }> = {
  product_received: { label: "Product received", icon: "cube" },
  market_research_started: { label: "Researching market", icon: "search" },
  market_research_done: { label: "Research complete", icon: "check" },
  strategy_generated: { label: "Strategy generated", icon: "lightning" },
  strategy_stored: { label: "Strategy stored", icon: "save" },
  agent_error: { label: "Error", icon: "error" },
  scout_status_change: { label: "Scout alert", icon: "alert" },
  pivot_email_drafted: { label: "Pivot drafted", icon: "mail" },
  outage_reprioritized: { label: "Outage reprioritized", icon: "zap" },
};

function StatusDot({ icon }: { icon: string }) {
  const isError = icon === "error";
  const isAlert = icon === "alert" || icon === "zap";
  const color = isError
    ? "bg-danger"
    : isAlert
      ? "bg-warning"
      : "bg-teal";
  return <span className={`w-1.5 h-1.5 rounded-full ${color} shrink-0`} />;
}

function formatData(data: Record<string, unknown>): string | null {
  const meaningful = Object.entries(data).filter(
    ([, v]) => v !== undefined && v !== null && v !== ""
  );
  if (meaningful.length === 0) return null;
  return meaningful
    .map(([k, v]) => {
      const val = typeof v === "object" ? JSON.stringify(v) : String(v);
      return `${k}: ${val}`;
    })
    .join(" / ");
}

export function ActivityFeed({ events }: { events?: ActivityEvent[] }) {
  const displayEvents = events ?? [];

  return (
    <div className="flex-1 overflow-y-auto -mx-5 px-5 space-y-1">
      {displayEvents.length === 0 ? (
        <p className="text-sm text-text-tertiary py-4 text-center">
          Waiting for activity...
        </p>
      ) : (
        displayEvents.map((e, i) => {
          const config = EVENT_CONFIG[e.type] ?? { label: e.type, icon: "dot" };
          const time = new Date(e.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          });
          const detail = formatData(e.data);
          const isError = e.type === "agent_error";

          return (
            <div
              key={`${e.timestamp}-${i}`}
              className={`flex items-start gap-3 py-2.5 px-3 rounded-lg text-sm transition-colors ${
                isError ? "bg-danger/5" : "hover:bg-surface-overlay"
              }`}
            >
              <div className="pt-1.5">
                <StatusDot icon={config.icon} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline justify-between gap-2">
                  <span className={`font-medium text-xs ${isError ? "text-danger" : "text-text-primary"}`}>
                    {config.label}
                  </span>
                  <span className="text-[10px] text-text-tertiary tabular-nums shrink-0">
                    {time}
                  </span>
                </div>
                {detail && (
                  <p className="text-xs text-text-secondary mt-0.5 truncate">
                    {detail}
                  </p>
                )}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
