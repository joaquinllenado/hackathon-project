import { useState, useEffect, useCallback } from "react";
import { fetchLeads } from "../api/client";
import type { Lead } from "../types/api";

function ScorePill({ score }: { score?: number }) {
  const s = score ?? 0;
  const color =
    s >= 70
      ? "text-success"
      : s >= 50
        ? "text-warning"
        : "text-danger";

  return (
    <span className={`text-sm font-semibold tabular-nums ${color}`}>
      {s}
    </span>
  );
}

export function LeadsTable({ refreshTrigger }: { refreshTrigger?: number }) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { leads: data } = await fetchLeads();
      setLeads(data ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load leads");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshTrigger]);

  if (loading && leads.length === 0) {
    return <p className="text-sm text-text-tertiary py-2">Loading leads...</p>;
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

  if (leads.length === 0) {
    return (
      <p className="text-sm text-text-tertiary py-2">
        No leads yet. Generate a strategy first.
      </p>
    );
  }

  return (
    <div className="space-y-1 -mx-5">
      {leads.map((lead) => (
        <div
          key={lead.domain}
          className="flex items-center gap-4 px-5 py-3 hover:bg-surface-overlay transition-colors"
        >
          <div className="w-8 h-8 rounded-lg bg-surface-overlay border border-border-subtle flex items-center justify-center text-xs font-semibold text-text-secondary uppercase">
            {lead.name.slice(0, 2)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-medium text-text-primary truncate">
                {lead.name}
              </span>
              <span className="text-xs text-text-tertiary truncate">
                {lead.domain}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-0.5">
              {Array.isArray(lead.tech_stack) && lead.tech_stack.length > 0 && (
                <span className="text-xs text-text-tertiary truncate">
                  {lead.tech_stack.slice(0, 3).join(", ")}
                  {lead.tech_stack.length > 3 && ` +${lead.tech_stack.length - 3}`}
                </span>
              )}
              {lead.employees != null && (
                <span className="text-xs text-text-tertiary">
                  {lead.employees.toLocaleString()} emp
                </span>
              )}
              {lead.funding && (
                <span className="text-xs text-text-tertiary">
                  {lead.funding}
                </span>
              )}
            </div>
          </div>
          <ScorePill score={lead.score} />
        </div>
      ))}
    </div>
  );
}
