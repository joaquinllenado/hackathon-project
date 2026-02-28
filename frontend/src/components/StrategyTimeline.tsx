import { useState, useEffect, useCallback } from "react";
import { fetchGraph } from "../api/client";
import type { GraphNode } from "../types/api";

function strategyFromGraph(nodes: GraphNode[]): GraphNode[] {
  return nodes
    .filter((n) => n.type === "strategy")
    .sort((a, b) => (b.version ?? 0) - (a.version ?? 0));
}

export function StrategyTimeline({ refreshTrigger }: { refreshTrigger?: number }) {
  const [strategies, setStrategies] = useState<GraphNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { nodes } = await fetchGraph();
      setStrategies(strategyFromGraph(nodes ?? []));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load timeline");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshTrigger]);

  if (loading && strategies.length === 0) {
    return <p className="text-sm text-text-tertiary py-2">Loading timeline...</p>;
  }

  if (error) {
    return (
      <div className="flex items-center justify-between">
        <span className="text-xs text-danger">{error}</span>
        <button onClick={load} className="text-[10px] text-text-secondary hover:text-text-primary">
          Retry
        </button>
      </div>
    );
  }

  if (strategies.length === 0) {
    return (
      <p className="text-sm text-text-tertiary py-2">
        No strategy history yet.
      </p>
    );
  }

  return (
    <div className="space-y-0">
      {strategies.map((s, i) => {
        const isLatest = i === 0;
        return (
          <div key={s.id} className="flex gap-3">
            <div className="flex flex-col items-center pt-1">
              <div
                className={`w-2.5 h-2.5 rounded-full border-2 shrink-0 ${
                  isLatest
                    ? "bg-accent border-accent"
                    : "bg-transparent border-text-tertiary"
                }`}
              />
              {i < strategies.length - 1 && (
                <div className="w-px flex-1 bg-border-default my-1" />
              )}
            </div>
            <div className="flex-1 pb-4">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-semibold ${isLatest ? "text-accent" : "text-text-secondary"}`}>
                  v{s.version}
                </span>
                {s.created_at && (
                  <span className="text-[10px] text-text-tertiary">
                    {new Date(s.created_at).toLocaleString([], {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                )}
              </div>
              {s.icp && (
                <p className="text-xs text-text-secondary mt-1 line-clamp-2 leading-relaxed">
                  {s.icp}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
