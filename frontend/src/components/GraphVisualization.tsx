import { useState, useEffect, useCallback, useRef } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { fetchGraph } from "../api/client";
import type { GraphNode, GraphLink } from "../types/api";

const NODE_COLORS: Record<string, string> = {
  strategy: "#6366f1",
  company: "#22c55e",
  evidence: "#64748b",
  lesson: "#f59e0b",
};

const NODE_LABELS: Record<string, string> = {
  strategy: "Strategy",
  company: "Company",
  evidence: "Evidence",
  lesson: "Lesson",
};

export function GraphVisualization({ refreshTrigger }: { refreshTrigger?: number }) {
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] }>({
    nodes: [],
    links: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      setDimensions({
        width: entry.contentRect.width,
        height: 400,
      });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchGraph();
      setGraphData({ nodes: data.nodes ?? [], links: data.links ?? [] });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load graph");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshTrigger]);

  if (loading && graphData.nodes.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center text-text-tertiary text-sm">
        Loading graph...
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-[400px] flex flex-col items-center justify-center gap-2">
        <span className="text-xs text-danger">{error}</span>
        <button
          onClick={load}
          className="text-xs text-text-secondary hover:text-text-primary transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (graphData.nodes.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center text-text-tertiary text-sm">
        No graph data yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        {Object.entries(NODE_LABELS).map(([type, label]) => (
          <div key={type} className="flex items-center gap-1.5 text-xs text-text-tertiary">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: NODE_COLORS[type] }}
            />
            {label}
          </div>
        ))}
      </div>

      <div
        ref={containerRef}
        className="h-[400px] w-full rounded-lg overflow-hidden bg-[#08080d] border border-border-subtle"
      >
        <ForceGraph2D
          graphData={{
            nodes: graphData.nodes.map((n) => ({
              ...n,
              color: NODE_COLORS[n.type] ?? "#64748b",
            })),
            links: graphData.links,
          }}
          width={dimensions.width}
          height={dimensions.height}
          nodeId="id"
          nodeLabel={(n) => {
            const node = n as GraphNode;
            return node.label ?? node.id;
          }}
          nodeColor={(n) => (n as GraphNode & { color: string }).color}
          nodeRelSize={5}
          linkColor={() => "rgba(255,255,255,0.06)"}
          linkWidth={1}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          linkDirectionalArrowColor={() => "rgba(255,255,255,0.1)"}
          onNodeClick={(n) => setSelectedNode(n as GraphNode)}
          onBackgroundClick={() => setSelectedNode(null)}
          backgroundColor="transparent"
        />
      </div>

      {selectedNode && (
        <div className="p-4 rounded-lg bg-surface-overlay border border-border-subtle">
          <div className="flex items-center gap-2 mb-2">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: NODE_COLORS[selectedNode.type] }}
            />
            <span className="text-sm font-medium text-text-primary">
              {selectedNode.label}
            </span>
            <span className="text-xs text-text-tertiary capitalize">
              {selectedNode.type}
            </span>
          </div>
          {selectedNode.icp && (
            <p className="text-xs text-text-secondary leading-relaxed">{selectedNode.icp}</p>
          )}
          {selectedNode.details && (
            <p className="text-xs text-text-secondary leading-relaxed">{selectedNode.details}</p>
          )}
          {selectedNode.domain && (
            <p className="text-xs text-text-tertiary mt-1">{selectedNode.domain}</p>
          )}
          {selectedNode.summary && (
            <p className="text-xs text-text-secondary leading-relaxed mt-1">{selectedNode.summary}</p>
          )}
        </div>
      )}
    </div>
  );
}
