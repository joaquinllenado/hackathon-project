import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { fetchGraph } from "../api/client";
import type { GraphNode } from "../types/api";

type Classification = "Strike" | "Monitor" | "Disregard" | "Unclassified";

const CLASSIFICATION_COLORS: Record<Classification, string> = {
  Strike: "#22c55e",
  Monitor: "#f59e0b",
  Disregard: "#ef4444",
  Unclassified: "#64748b",
};

const STRATEGY_COLOR = "#6366f1";
const EVIDENCE_COLOR = "#94a3b8";
const LESSON_COLOR = "#f59e0b";

const NODE_SIZE = 5;

function getCompanyClassification(node: GraphNode): Classification {
  const c = node.classification;
  if (c === "Strike" || c === "Monitor" || c === "Disregard") return c;
  return "Unclassified";
}

function drawSquare(ctx: CanvasRenderingContext2D, x: number, y: number, size: number, color: string) {
  ctx.fillStyle = color;
  ctx.fillRect(x - size, y - size, size * 2, size * 2);
  ctx.strokeStyle = "rgba(255,255,255,0.3)";
  ctx.lineWidth = 0.5;
  ctx.strokeRect(x - size, y - size, size * 2, size * 2);
}

function drawDiamond(ctx: CanvasRenderingContext2D, x: number, y: number, size: number, color: string) {
  ctx.beginPath();
  ctx.moveTo(x, y - size);
  ctx.lineTo(x + size, y);
  ctx.lineTo(x, y + size);
  ctx.lineTo(x - size, y);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.3)";
  ctx.lineWidth = 0.5;
  ctx.stroke();
}

function drawTriangle(ctx: CanvasRenderingContext2D, x: number, y: number, size: number, color: string) {
  ctx.beginPath();
  ctx.moveTo(x, y - size);
  ctx.lineTo(x + size, y + size * 0.7);
  ctx.lineTo(x - size, y + size * 0.7);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.3)";
  ctx.lineWidth = 0.5;
  ctx.stroke();
}

function drawCircle(ctx: CanvasRenderingContext2D, x: number, y: number, size: number, color: string) {
  ctx.beginPath();
  ctx.arc(x, y, size, 0, 2 * Math.PI);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.15)";
  ctx.lineWidth = 0.5;
  ctx.stroke();
}

interface RawEdge {
  source: string;
  target: string;
  type: string;
}

export function GraphVisualization({ refreshTrigger }: { refreshTrigger?: number }) {
  const [fullNodes, setFullNodes] = useState<GraphNode[]>([]);
  const [rawEdges, setRawEdges] = useState<RawEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [expandedCompany, setExpandedCompany] = useState<string | null>(null);
  const [activeFilters, setActiveFilters] = useState<Set<Classification>>(
    new Set(["Strike", "Monitor", "Disregard", "Unclassified"])
  );
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      setDimensions({ width: entry.contentRect.width, height: 400 });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchGraph();
      setFullNodes(data.nodes ?? []);
      setRawEdges(
        (data.links ?? []).map((l) => ({
          source: typeof l.source === "object" ? (l.source as GraphNode).id : l.source,
          target: typeof l.target === "object" ? (l.target as GraphNode).id : l.target,
          type: l.type,
        }))
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load graph");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshTrigger]);

  const latestStrategyId = useMemo(() => {
    let best: GraphNode | null = null;
    for (const n of fullNodes) {
      if (n.type === "strategy") {
        if (!best || (n.version ?? 0) > (best.version ?? 0)) best = n;
      }
    }
    return best?.id ?? null;
  }, [fullNodes]);

  const expandedIds = useMemo(() => {
    if (!expandedCompany) return new Set<string>();

    const adj = new Map<string, Set<string>>();
    const addEdge = (a: string, b: string) => {
      if (!adj.has(a)) adj.set(a, new Set());
      adj.get(a)!.add(b);
      if (!adj.has(b)) adj.set(b, new Set());
      adj.get(b)!.add(a);
    };
    for (const e of rawEdges) addEdge(e.source, e.target);

    const nodeById = new Map(fullNodes.map((n) => [n.id, n]));
    const result = new Set<string>();

    const hop1 = adj.get(expandedCompany) ?? new Set();
    for (const id of hop1) {
      const n = nodeById.get(id);
      if (n && (n.type === "evidence" || n.type === "lesson")) result.add(id);
    }

    for (const id of hop1) {
      const n = nodeById.get(id);
      if (!n || n.type !== "strategy") continue;
      const hop2 = adj.get(id) ?? new Set();
      for (const id2 of hop2) {
        const n2 = nodeById.get(id2);
        if (n2 && (n2.type === "evidence" || n2.type === "lesson")) result.add(id2);
      }
    }

    return result;
  }, [expandedCompany, rawEdges, fullNodes]);

  const filteredData = useMemo(() => {
    const visibleNodeIds = new Set<string>();

    for (const node of fullNodes) {
      if (node.type === "strategy" && node.id === latestStrategyId) {
        visibleNodeIds.add(node.id);
      } else if (node.type === "company") {
        const cls = getCompanyClassification(node);
        if (activeFilters.has(cls)) visibleNodeIds.add(node.id);
      } else if (
        (node.type === "evidence" || node.type === "lesson") &&
        expandedIds.has(node.id)
      ) {
        visibleNodeIds.add(node.id);
      }
    }

    const nodes = fullNodes.filter((n) => visibleNodeIds.has(n.id));
    const links = rawEdges
      .filter((e) => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target))
      .map((e) => ({ ...e }));
    return { nodes, links };
  }, [fullNodes, rawEdges, activeFilters, expandedIds, latestStrategyId]);

  const toggleFilter = (cls: Classification) => {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (next.has(cls)) next.delete(cls);
      else next.add(cls);
      return next;
    });
  };

  const handleNodeClick = useCallback(
    (raw: object) => {
      const node = raw as GraphNode;
      setSelectedNode(node);
      if (node.type === "company") {
        setExpandedCompany((prev) => (prev === node.id ? null : node.id));
      }
    },
    []
  );

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null);
    setExpandedCompany(null);
  }, []);

  const paintNode = useCallback(
    (raw: object, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const node = raw as GraphNode & { x?: number; y?: number };
      const x = node.x ?? 0;
      const y = node.y ?? 0;
      const size = NODE_SIZE / globalScale * 1.8;
      const isExpanded = node.id === expandedCompany;

      if (node.type === "strategy") {
        drawSquare(ctx, x, y, size * 1.2, STRATEGY_COLOR);
      } else if (node.type === "company") {
        const cls = getCompanyClassification(node);
        const color = CLASSIFICATION_COLORS[cls];
        drawCircle(ctx, x, y, size, color);
        if (isExpanded) {
          ctx.beginPath();
          ctx.arc(x, y, size + 2 / globalScale, 0, 2 * Math.PI);
          ctx.strokeStyle = color;
          ctx.lineWidth = 1.5 / globalScale;
          ctx.stroke();
        }
      } else if (node.type === "evidence") {
        drawDiamond(ctx, x, y, size, EVIDENCE_COLOR);
      } else if (node.type === "lesson") {
        drawTriangle(ctx, x, y, size * 1.1, LESSON_COLOR);
      }

      if (globalScale > 1.5) {
        const labelText = node.label ?? "";
        const maxLen = 18;
        const label = labelText.length > maxLen ? labelText.slice(0, maxLen) + "..." : labelText;
        ctx.font = `${10 / globalScale}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillStyle = "rgba(255,255,255,0.7)";
        ctx.fillText(label, x, y + size + 2 / globalScale);
      }
    },
    [expandedCompany]
  );

  if (loading && fullNodes.length === 0) {
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
        <button onClick={load} className="text-xs text-text-secondary hover:text-text-primary transition-colors">
          Retry
        </button>
      </div>
    );
  }

  if (fullNodes.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center text-text-tertiary text-sm">
        No graph data yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Legend & Filters */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
        <div className="flex items-center gap-4 mr-4">
          <LegendItem shape="square" color={STRATEGY_COLOR} label="Strategy" />
          <LegendItem shape="diamond" color={EVIDENCE_COLOR} label="Evidence" />
          <LegendItem shape="triangle" color={LESSON_COLOR} label="Lesson" />
        </div>
        <div className="h-4 w-px bg-border-subtle" />
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-text-tertiary uppercase tracking-wider mr-1">Filter leads</span>
          {(Object.keys(CLASSIFICATION_COLORS) as Classification[]).map((cls) => (
            <button
              key={cls}
              type="button"
              onClick={() => toggleFilter(cls)}
              className={`text-[11px] font-medium px-2.5 py-1 rounded-full border transition-all ${
                activeFilters.has(cls)
                  ? "border-current opacity-100"
                  : "border-border-subtle opacity-40"
              }`}
              style={{ color: CLASSIFICATION_COLORS[cls] }}
            >
              {cls}
            </button>
          ))}
        </div>
      </div>

      <div
        ref={containerRef}
        className="h-[400px] w-full rounded-lg overflow-hidden bg-[#08080d] border border-border-subtle"
      >
        <ForceGraph2D
          graphData={filteredData}
          width={dimensions.width}
          height={dimensions.height}
          nodeId="id"
          nodeLabel={(n) => {
            const node = n as GraphNode;
            return node.label ?? node.id;
          }}
          nodeCanvasObject={paintNode}
          nodePointerAreaPaint={(raw, color, ctx) => {
            const node = raw as GraphNode & { x?: number; y?: number };
            const x = node.x ?? 0;
            const y = node.y ?? 0;
            ctx.beginPath();
            ctx.arc(x, y, NODE_SIZE, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
          }}
          linkColor={() => "rgba(255,255,255,0.25)"}
          linkWidth={1.5}
          linkDirectionalArrowLength={3.5}
          linkDirectionalArrowRelPos={1}
          linkDirectionalArrowColor={() => "rgba(255,255,255,0.35)"}
          onNodeClick={handleNodeClick}
          onBackgroundClick={handleBackgroundClick}
          backgroundColor="transparent"
        />
      </div>

      {expandedCompany && (
        <p className="text-[10px] text-text-tertiary">
          Showing evidence &amp; lessons for selected company. Click background to collapse.
        </p>
      )}

      {selectedNode && (
        <div className="p-4 rounded-lg bg-surface-overlay border border-border-subtle">
          <div className="flex items-center gap-2 mb-2">
            <NodeIndicator type={selectedNode.type} classification={selectedNode.classification} />
            <span className="text-sm font-medium text-text-primary">{selectedNode.label}</span>
            <span className="text-xs text-text-tertiary capitalize">{selectedNode.type}</span>
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
          {selectedNode.classification && (
            <p className="text-xs text-text-secondary mt-1">
              Classification: <span className="font-semibold">{selectedNode.classification}</span>
            </p>
          )}
          {selectedNode.summary && (
            <p className="text-xs text-text-secondary leading-relaxed mt-1">{selectedNode.summary}</p>
          )}
          {Array.isArray(selectedNode.tech_stack) && selectedNode.tech_stack.length > 0 && (
            <p className="text-xs text-text-tertiary mt-1">
              Tech: {selectedNode.tech_stack.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function LegendItem({ shape, color, label }: { shape: "square" | "diamond" | "triangle"; color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5 text-xs text-text-tertiary">
      <svg width="10" height="10" viewBox="0 0 10 10">
        {shape === "square" && <rect x="1" y="1" width="8" height="8" fill={color} rx="1" />}
        {shape === "diamond" && <polygon points="5,0 10,5 5,10 0,5" fill={color} />}
        {shape === "triangle" && <polygon points="5,0 10,9 0,9" fill={color} />}
      </svg>
      {label}
    </div>
  );
}

function NodeIndicator({ type, classification }: { type: string; classification?: string }) {
  let color: string;
  if (type === "strategy") color = STRATEGY_COLOR;
  else if (type === "evidence") color = EVIDENCE_COLOR;
  else if (type === "lesson") color = LESSON_COLOR;
  else {
    const cls = (classification ?? "Unclassified") as Classification;
    color = CLASSIFICATION_COLORS[cls] ?? CLASSIFICATION_COLORS.Unclassified;
  }
  return (
    <span className="w-2 h-2 rounded-sm inline-block" style={{ backgroundColor: color }} />
  );
}
