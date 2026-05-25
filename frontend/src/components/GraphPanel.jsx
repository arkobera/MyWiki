import { startTransition, useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  ReactFlow,
} from "@xyflow/react";
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
} from "d3-force";
import "@xyflow/react/dist/style.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

const KIND_THEME = {
  category: {
    card: "border-amber-300/75 bg-amber-400/12 text-amber-50",
    chip: "bg-amber-300/18 text-amber-100",
    minimap: "#f59e0b",
  },
  concept: {
    card: "border-orange-300/75 bg-orange-400/12 text-orange-50",
    chip: "bg-orange-300/18 text-orange-100",
    minimap: "#fb923c",
  },
  document: {
    card: "border-cyan-300/75 bg-cyan-400/12 text-cyan-50",
    chip: "bg-cyan-300/18 text-cyan-100",
    minimap: "#22d3ee",
  },
  keyword: {
    card: "border-violet-300/75 bg-violet-400/12 text-violet-50",
    chip: "bg-violet-300/18 text-violet-100",
    minimap: "#c084fc",
  },
  file: {
    card: "border-emerald-300/75 bg-emerald-400/12 text-emerald-50",
    chip: "bg-emerald-300/18 text-emerald-100",
    minimap: "#34d399",
  },
  embedding: {
    card: "border-sky-300/75 bg-sky-400/12 text-sky-50",
    chip: "bg-sky-300/18 text-sky-100",
    minimap: "#38bdf8",
  },
  default: {
    card: "border-slate-300/60 bg-slate-400/10 text-slate-50",
    chip: "bg-slate-300/15 text-slate-100",
    minimap: "#94a3b8",
  },
};

function nodeRadius(kind) {
  if (kind === "document") {
    return 180;
  }
  if (kind === "category") {
    return 135;
  }
  if (kind === "concept") {
    return 110;
  }
  return 100;
}

function anchorForKind(kind) {
  if (kind === "category") {
    return { x: -620, y: -80 };
  }
  if (kind === "document") {
    return { x: -80, y: 0 };
  }
  if (kind === "keyword") {
    return { x: 460, y: -120 };
  }
  if (kind === "concept") {
    return { x: 860, y: 120 };
  }
  return { x: 0, y: 0 };
}

function layoutGraph(sourceNodes, sourceEdges) {
  const safeNodes = sourceNodes.map((node, index) => ({
    ...node,
    position: {
      x: Number.isFinite(node.position?.x) ? node.position.x : 0,
      y: Number.isFinite(node.position?.y) ? node.position.y : 0,
    },
    __layoutIndex: index,
  }));

  const width = 960;
  const height = 540;

  const bounds = safeNodes.reduce(
    (acc, node) => {
      const x = node.position.x;
      const y = node.position.y;
      return {
        minX: Math.min(acc.minX, x),
        maxX: Math.max(acc.maxX, x),
        minY: Math.min(acc.minY, y),
        maxY: Math.max(acc.maxY, y),
      };
    },
    { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity }
  );

  const graphWidth = Math.max(bounds.maxX - bounds.minX, 160);
  const graphHeight = Math.max(bounds.maxY - bounds.minY, 160);
  const scale = Math.min((width - 120) / graphWidth, (height - 120) / graphHeight, 1);

  const centerX = (bounds.minX + bounds.maxX) / 2;
  const centerY = (bounds.minY + bounds.maxY) / 2;
  const targetCenterX = width / 2;
  const targetCenterY = height / 2;

  const positionedNodes = safeNodes.map((node) => ({
    ...node,
    position: {
      x: Math.round((node.position.x - centerX) * scale + targetCenterX),
      y: Math.round((node.position.y - centerY) * scale + targetCenterY),
    },
  }));

  return {
    nodes: positionedNodes,
    edges: sourceEdges,
  };
}

function KnowledgeNode({ data, selected }) {
  const kind = data.kind || "default";
  const theme = KIND_THEME[kind] || KIND_THEME.default;

  return (
    <div
      className={`w-[260px] rounded-[24px] border px-4 py-3 shadow-[0_24px_80px_rgba(15,23,42,0.42)] backdrop-blur transition ${theme.card} ${selected ? "ring-2 ring-white/60" : ""}`}
    >
      <Handle type="target" position="left" className="!h-2 !w-2 !border-0 !bg-white/40" />
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-white/70">
            {kind}
          </p>
          <div className="mt-2 text-sm font-semibold leading-5 text-white">
            {data.label}
          </div>
        </div>

        {data.category ? (
          <span className={`rounded-full px-2 py-1 text-[10px] font-medium ${theme.chip}`}>
            {data.category}
          </span>
        ) : null}
      </div>

      {data.summary ? (
        <p className="mt-3 text-xs leading-5 text-slate-100/88">
          {String(data.summary).slice(0, 160)}
        </p>
      ) : null}

      {data.source_file ? (
        <p className="mt-3 text-[11px] leading-5 text-slate-200/80">
          <span className="font-semibold text-white">Source:</span> {data.source_file}
        </p>
      ) : null}

      {data.embedding_id ? (
        <p className="mt-1 text-[11px] leading-5 text-slate-200/80">
          <span className="font-semibold text-white">Embedding:</span> {data.embedding_id}
        </p>
      ) : null}

      {data.document_count ? (
        <p className="mt-1 text-[11px] leading-5 text-slate-200/80">
          <span className="font-semibold text-white">Shared by:</span> {data.document_count} document
          {data.document_count === 1 ? "" : "s"}
        </p>
      ) : null}

      {data.keyword_count ? (
        <p className="mt-1 text-[11px] leading-5 text-slate-200/80">
          <span className="font-semibold text-white">Keywords:</span> {data.keyword_count}
        </p>
      ) : null}
      <Handle type="source" position="right" className="!h-2 !w-2 !border-0 !bg-white/40" />
    </div>
  );
}

const nodeTypes = {
  category: KnowledgeNode,
  concept: KnowledgeNode,
  document: KnowledgeNode,
  keyword: KnowledgeNode,
  file: KnowledgeNode,
  embedding: KnowledgeNode,
  meta: KnowledgeNode,
  default: KnowledgeNode,
};

function formatInspectorLabel(edge) {
  if (!edge) {
    return null;
  }

  const sharedConcepts = edge.data?.shared_concepts || [];
  const sharedKeywords = edge.data?.shared_keywords || [];
  const pieces = [];

  if (sharedConcepts.length) {
    pieces.push(`Shared concepts: ${sharedConcepts.join(", ")}`);
  }
  if (sharedKeywords.length) {
    pieces.push(`Shared keywords: ${sharedKeywords.join(", ")}`);
  }
  if (edge.data?.same_category) {
    pieces.push("Same category");
  }

  return pieces.join(" • ") || edge.label;
}

export default function GraphPanel({ refreshKey = "" }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [status, setStatus] = useState("Loading graph…");
  const [graphMeta, setGraphMeta] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let ignore = false;

    const loadGraph = async () => {
      if (!ignore) {
        setIsLoading(true);
      }

      try {
        const response = await fetch(`${API_BASE_URL}/knowledge-graph`, {
          cache: "no-store",
        });
        const payload = await response.json();

        if (!response.ok) {
          throw new Error(payload.detail || "Unable to load the knowledge graph.");
        }

        if (ignore) {
          return;
        }

        const layouted = layoutGraph(payload.nodes || [], payload.edges || []);
        const nextEdges = layouted.edges.map((edge) => ({
          ...edge,
          label: "",
        }));

        startTransition(() => {
          setNodes(layouted.nodes);
          setEdges(nextEdges);
          setGraphMeta(payload.meta || null);
          setSelectedNode(null);
          setSelectedEdge(null);
        });

        setStatus(
          payload.meta?.document_count
            ? `Loaded ${payload.meta.document_count} indexed document${payload.meta.document_count === 1 ? "" : "s"} from Agents/graph.json.`
            : "No knowledge graph data is available yet."
        );
      } catch (error) {
        if (!ignore) {
          setNodes([]);
          setEdges([]);
          setGraphMeta(null);
          setStatus(error.message || "Unable to load the knowledge graph.");
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    };

    loadGraph();

    return () => {
      ignore = true;
    };
  }, [refreshKey]);

  const hasGraphData = nodes.length > 0;

  const fitViewOptions = useMemo(
    () => ({
      padding: 0.2,
      duration: 250,
      maxZoom: 1.2,
    }),
    []
  );

  const inspectorText = selectedNode
    ? selectedNode.data?.summary ||
      selectedNode.data?.source_file ||
      selectedNode.data?.embedding_path ||
      "This node does not have extra detail yet."
    : formatInspectorLabel(selectedEdge);

  return (
    <section className="flex w-full min-h-[420px] flex-1 flex-col overflow-hidden rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,_rgba(15,23,42,0.95),_rgba(2,6,23,0.96))] shadow-[0_24px_80px_rgba(2,6,23,0.45)]">
      <div className="border-b border-white/8 px-6 py-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-violet-300/75">
              Graph
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
              Knowledge graph
            </h2>
            <p className="mt-2 text-sm text-slate-300">{status}</p>
          </div>

          {graphMeta ? (
            <div className="grid grid-cols-3 gap-2 text-center text-[11px] text-slate-200">
              <div className="rounded-2xl border border-white/8 bg-white/[0.04] px-3 py-2">
                <div className="text-lg font-semibold text-white">{graphMeta.document_count}</div>
                <div>Documents</div>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.04] px-3 py-2">
                <div className="text-lg font-semibold text-white">{graphMeta.node_count}</div>
                <div>Nodes</div>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.04] px-3 py-2">
                <div className="text-lg font-semibold text-white">{graphMeta.edge_count}</div>
                <div>Edges</div>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="flex flex-1 min-h-0 flex-col">
        {isLoading ? (
          <div className="flex flex-1 items-center justify-center px-6 py-8 text-center text-xl font-medium text-slate-400">
            Loading data…
          </div>
        ) : hasGraphData ? (
          <>
            <div className="min-h-0 flex-1">
              <div className="h-[clamp(420px,56vh,760px)] w-full min-w-0">
                <ReactFlow
                  nodes={nodes}
                  edges={edges}
                  nodeTypes={nodeTypes}
                  fitView
                  fitViewOptions={fitViewOptions}
                  nodesDraggable
                  panOnScroll
                  zoomOnScroll
                  onNodeClick={(_, node) => {
                    setSelectedNode(node);
                    setSelectedEdge(null);
                  }}
                  onEdgeClick={(_, edge) => {
                    setSelectedEdge(edge);
                    setSelectedNode(null);
                  }}
                  onPaneClick={() => {
                    setSelectedNode(null);
                    setSelectedEdge(null);
                  }}
                  className="bg-slate-950/65"
                  style={{ width: "100%", height: "100%" }}
                >
                <Background gap={20} size={1} color="rgba(148, 163, 184, 0.18)" />
                <MiniMap
                  nodeColor={(node) =>
                    (KIND_THEME[node.data?.kind] || KIND_THEME.default).minimap
                  }
                  maskColor="rgba(15, 23, 42, 0.72)"
                  bgColor="rgba(2, 6, 23, 0.96)"
                  style={{
                    background: "rgba(2, 6, 23, 0.96)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 16,
                  }}
                  pannable
                  zoomable
                />
                <Controls position="bottom-right" />
                </ReactFlow>
              </div>
            </div>

            <aside className="border-t border-white/8 bg-slate-950/45 px-5 py-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-cyan-300/70">
                Inspector
              </p>
              <h3 className="mt-3 text-lg font-semibold text-white">
                {selectedNode?.data?.label || selectedEdge?.label || "Explore the graph"}
              </h3>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                {inspectorText ||
                  "Select a node to inspect its summary and metadata, or pick a document edge to see why two files were connected."}
              </p>
            </aside>
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center px-6 py-8 text-center text-xl font-medium text-slate-400">
            No graph data available yet.
          </div>
        )}
      </div>
    </section>
  );
}
