import { useState } from "react";
import { postReset } from "../api/client";

export function ResetButton({ onReset }: { onReset: () => void }) {
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const handleClick = async () => {
    if (!confirming) {
      setConfirming(true);
      setTimeout(() => setConfirming(false), 3000);
      return;
    }
    setConfirming(false);
    setLoading(true);
    try {
      await postReset();
      onReset();
    } catch {
      // error will show in activity feed via broadcast
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      className={`px-3.5 py-2 text-xs font-medium rounded-lg transition-all border ${
        confirming
          ? "bg-danger/10 text-danger border-danger/30 hover:bg-danger/20"
          : "bg-surface-overlay text-text-secondary border-border-subtle hover:text-text-primary hover:border-border-default"
      } disabled:opacity-40`}
    >
      {loading ? "Resetting..." : confirming ? "Confirm reset?" : "Reset"}
    </button>
  );
}
