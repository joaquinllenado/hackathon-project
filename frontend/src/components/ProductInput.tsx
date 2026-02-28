import { useState, useCallback, useRef } from "react";
import { postProduct, transcribeAudio } from "../api/client";
import { extractTranscript } from "../utils/transcript";

const MAX_LENGTH = 10_000;

export function ProductInput() {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const handleSubmit = useCallback(async () => {
    const text = description.trim();
    if (!text) return;
    setError(null);
    setLoading(true);
    try {
      await postProduct(text);
      setDescription("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit");
    } finally {
      setLoading(false);
    }
  }, [description]);

  const startRecording = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/mp4";
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        if (chunksRef.current.length === 0) return;
        const blob = new Blob(chunksRef.current, { type: mimeType });
        setLoading(true);
        try {
          const result = await transcribeAudio(blob);
          const transcript = extractTranscript(result);
          if (transcript) {
            setDescription((prev) => {
              const combined = prev ? `${prev}\n${transcript}` : transcript;
              return combined.slice(0, MAX_LENGTH);
            });
          }
        } catch (e) {
          setError(e instanceof Error ? e.message : "Transcription failed");
        } finally {
          setLoading(false);
        }
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not access microphone");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    setRecording(false);
  }, []);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value.slice(0, MAX_LENGTH))}
            placeholder="Describe your product to find ideal customers..."
            className="w-full min-h-[48px] px-4 py-3 rounded-xl bg-surface-overlay border border-border-default text-text-primary placeholder-text-tertiary text-sm leading-relaxed focus:outline-none focus:ring-1 focus:ring-teal focus:border-teal resize-none transition-all"
            disabled={loading}
            rows={2}
          />
          <span className="absolute bottom-2 right-3 text-[10px] text-text-tertiary tabular-nums">
            {description.length.toLocaleString()}
          </span>
        </div>
        <button
          type="button"
          onClick={recording ? stopRecording : startRecording}
          disabled={loading}
          className={`shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-all ${
            recording
              ? "bg-danger/20 text-danger ring-1 ring-danger/40"
              : "bg-surface-overlay border border-border-default text-text-secondary hover:text-text-primary hover:border-border-default"
          }`}
          title={recording ? "Stop recording" : "Record with microphone"}
        >
          {recording ? (
            <span className="w-3.5 h-3.5 rounded-sm bg-danger animate-pulse" />
          ) : (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          )}
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={loading || !description.trim()}
          className="shrink-0 px-5 h-12 bg-accent hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-xl transition-all"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Running
            </span>
          ) : (
            "Hunt"
          )}
        </button>
      </div>
      {error && (
        <p className="text-xs text-danger pl-1">{error}</p>
      )}
    </div>
  );
}
