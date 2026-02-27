import { useState, useEffect, useCallback } from "react";
import { fetchStrategy } from "../api/client";
import type { Strategy } from "../types/api";

export function StrategyPanel({ refreshTrigger }: { refreshTrigger?: number }) {
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { strategy: data } = await fetchStrategy();
      setStrategy(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load strategy");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshTrigger]);

  if (loading && !strategy) {
    return <EmptyState text="Loading strategy..." />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-between">
        <span className="text-xs text-danger">{error}</span>
        <RetryButton onClick={load} />
      </div>
    );
  }

  if (!strategy) {
    return <EmptyState text="No strategy yet. Describe your product above to generate one." />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-accent bg-accent-muted px-2 py-0.5 rounded-md">
          v{strategy.version}
        </span>
        {strategy.created_at && (
          <span className="text-xs text-text-tertiary">
            {new Date(strategy.created_at).toLocaleDateString()}
          </span>
        )}
      </div>

      <div>
        <Label>Ideal Customer Profile</Label>
        <p className="text-sm text-text-primary leading-relaxed">{strategy.icp}</p>
      </div>

      {strategy.keywords?.length > 0 && (
        <div>
          <Label>Keywords</Label>
          <div className="flex flex-wrap gap-1.5">
            {strategy.keywords.map((k) => (
              <Tag key={k} variant="accent">{k}</Tag>
            ))}
          </div>
        </div>
      )}

      {strategy.competitors?.length > 0 && (
        <div>
          <Label>Competitors</Label>
          <div className="flex flex-wrap gap-1.5">
            {strategy.competitors.map((c) => (
              <Tag key={c} variant="neutral">{c}</Tag>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-medium uppercase tracking-widest text-text-tertiary mb-1.5">
      {children}
    </p>
  );
}

function Tag({ children, variant }: { children: React.ReactNode; variant: "accent" | "neutral" }) {
  const cls =
    variant === "accent"
      ? "bg-accent-muted text-accent"
      : "bg-surface-overlay text-text-secondary border border-border-subtle";
  return (
    <span className={`inline-block px-2 py-0.5 rounded-md text-xs ${cls}`}>
      {children}
    </span>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="text-sm text-text-tertiary py-2">{text}</p>;
}

function RetryButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="text-[10px] text-text-secondary hover:text-text-primary transition-colors"
    >
      Retry
    </button>
  );
}
