import { useState } from "react";
import { Link } from "react-router-dom";
import { postSimulateOutage } from "../api/client";

const COMPETITORS = ["DigitalOcean", "Supabase", "AWS"] as const;

interface TriggerResult {
  competitor: string;
  promoted_count: number;
  promoted: { name: string; domain: string }[];
}

export function AdminPage() {
  const [loading, setLoading] = useState<string | null>(null);
  const [result, setResult] = useState<TriggerResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTrigger = async (competitor: string) => {
    setError(null);
    setResult(null);
    setLoading(competitor);
    try {
      const res = await postSimulateOutage(competitor);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Trigger failed");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-surface text-text-primary dot-grid flex flex-col items-center justify-center px-6">
      <div className="w-full max-w-md space-y-8">
        <div>
          <Link
            to="/"
            className="text-xs text-text-tertiary hover:text-text-secondary transition-colors"
          >
            &larr; Back to dashboard
          </Link>
          <h1 className="text-xl font-semibold tracking-tight mt-3">
            Simulate Outage
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Pick a provider to trigger an outage. Leads using that technology
            will be promoted to <strong>Strike</strong> priority.
          </p>
        </div>

        <div className="space-y-3">
          {COMPETITORS.map((comp) => (
            <button
              key={comp}
              type="button"
              disabled={loading !== null}
              onClick={() => handleTrigger(comp)}
              className="w-full flex items-center justify-between px-5 py-4 rounded-xl border border-border-subtle bg-surface-raised hover:bg-surface-overlay transition-all disabled:opacity-40 group"
            >
              <span className="text-sm font-medium">{comp} outage</span>
              {loading === comp ? (
                <span className="text-xs text-text-tertiary animate-pulse">
                  Running...
                </span>
              ) : (
                <span className="text-xs text-text-tertiary group-hover:text-accent transition-colors">
                  Trigger &rarr;
                </span>
              )}
            </button>
          ))}
        </div>

        {result && (
          <div className="rounded-xl border border-success/30 bg-success/5 p-5 space-y-3">
            <p className="text-sm font-medium text-success">
              {result.promoted_count} lead{result.promoted_count !== 1 && "s"}{" "}
              promoted to Strike
            </p>
            {result.promoted.length > 0 && (
              <ul className="space-y-1">
                {result.promoted.map((l) => (
                  <li
                    key={l.domain}
                    className="text-xs text-text-secondary flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-success" />
                    {l.name}{" "}
                    <span className="text-text-tertiary">({l.domain})</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-danger/30 bg-danger/5 p-4">
            <p className="text-sm text-danger">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
