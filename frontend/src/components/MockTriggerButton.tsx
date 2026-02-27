import { useState } from "react";
import { postMockTrigger } from "../api/client";

export function MockTriggerButton() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    setError(null);
    setLoading(true);
    try {
      await postMockTrigger({
        status: "critical_outage",
        competitor: "DigitalOcean",
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Trigger failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={handleClick}
        disabled={loading}
        className="px-3.5 py-2 text-xs font-medium rounded-lg bg-warning/10 text-warning hover:bg-warning/20 disabled:opacity-40 transition-all border border-warning/20"
      >
        {loading ? "Triggering..." : "Simulate Outage"}
      </button>
      {error && (
        <span className="absolute top-full right-0 mt-1 text-[10px] text-danger whitespace-nowrap">
          {error}
        </span>
      )}
    </div>
  );
}
