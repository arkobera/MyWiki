import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  ReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

function KnowledgeNode({ data }) {
  const kindStyles = {
    document: "border-cyan-300/60 bg-cyan-400/15 text-cyan-50",
    keyword: "border-violet-300/70 bg-violet-400/15 text-violet-50",
    category: "border-amber-300/70 bg-amber-400/15 text-amber-50",
    meta: "border-emerald-300/70 bg-emerald-400/15 text-emerald-50",
    default: "border-slate-300/60 bg-slate-400/10 text-slate-50",
  };

  const kind = data.kind || "default";

  return (
    <div
      className={`rounded-2xl border px-4 py-3 shadow-[0_24px_80px_rgba(15,23,42,0.45)] ${kindStyles[kind] || kindStyles.default}`}
    >
      <Handle type="target" position="left" className="!bg-transparent" />
      <p className="text-[10px] font-semibold uppercase tracking-[0.3em] text-white/75">
        {kind}
      </p>
      <div className="mt-2 text-sm font-semibold text-white">{data.label}</div>
      {data.summary ? (
        <p className="mt-2 max-w-[220px] text-xs leading-5 text-slate-100/90">
          {String(data.summary).slice(0, 120)}
        </p>
      ) : null}
      <Handle type="source" position="right" className="!bg-transparent" />
    </div>
  );
}

const nodeTypes = {
  document: KnowledgeNode,
  keyword: KnowledgeNode,
  category: KnowledgeNode,
  meta: KnowledgeNode,
  default: KnowledgeNode,
};

export default function GraphPanel() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [status, setStatus] = useState("Loading graph…");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let ignore = false;

    const loadGraph = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/knowledge-graph`);
        const payload = await response.json();

        if (!response.ok) {
          throw new Error(payload.detail || "Unable to load the knowledge graph.");
        }

        if (ignore) {
          return;
        }

        setNodes(payload.nodes || []);
        setEdges(payload.edges || []);
        setStatus(
          payload.nodes?.length
            ? "Knowledge graph loaded from Agents/index.md."
            : "No knowledge graph data is available yet."
        );
      } catch (error) {
        if (!ignore) {
          setNodes([]);
          setEdges([]);
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
  }, []);

  const hasGraphData = nodes.length > 0;

  const fitViewOptions = useMemo(
    () => ({
      padding: 0.24,
      duration: 200,
    }),
    []
  );

  return (
    <section className="flex h-full min-h-[420px] flex-col overflow-hidden rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,_rgba(15,23,42,0.95),_rgba(2,6,23,0.96))] shadow-[0_24px_80px_rgba(2,6,23,0.45)]">
      <div className="border-b border-white/8 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-violet-300/75">
          Graph
        </p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
          Knowledge graph
        </h2>
        <p className="mt-2 text-sm text-slate-300">{status}</p>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {isLoading ? (
          <div className="flex flex-1 items-center justify-center px-6 py-8 text-center text-xl font-medium text-slate-400">
            Loading data…
          </div>
        ) : hasGraphData ? (
          <div className="h-full w-full">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              fitView
              fitViewOptions={fitViewOptions}
              nodesDraggable
              panOnScroll
              zoomOnScroll
              className="bg-slate-950/70"
            >
              <Background gap={18} size={1} color="rgba(148, 163, 184, 0.18)" />
              <MiniMap
                nodeColor={(node) =>
                  node.data?.kind === "document"
                    ? "#22d3ee"
                    : node.data?.kind === "keyword"
                      ? "#c084fc"
                      : node.data?.kind === "category"
                        ? "#f59e0b"
                        : "#34d399"
                }
                maskColor="rgba(15, 23, 42, 0.7)"
                pannable
                zoomable
              />
              <Controls position="bottom-right" />
            </ReactFlow>
          </div>
        ) : (
          <div className="flex flex-1 items-center justify-center px-6 py-8 text-center text-xl font-medium text-slate-400">
            No graph data available yet.
          </div>
        )}
      </div>
    </section>
  );
}
