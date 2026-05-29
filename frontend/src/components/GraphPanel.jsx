import { startTransition, useEffect, useRef, useState } from "react";
import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";
import { requestJson } from "../lib/api";

cytoscape.use(dagre);

const KIND_THEME = {
  category: {
    border: "#fbbf24",
    fill: "rgba(251,191,36,0.14)",
    text: "#fef3c7",
  },
  concept: {
    border: "#fb923c",
    fill: "rgba(251,146,60,0.14)",
    text: "#ffedd5",
  },
  document: {
    border: "#22d3ee",
    fill: "rgba(34,211,238,0.15)",
    text: "#cffafe",
  },
  embedding: {
    border: "#38bdf8",
    fill: "rgba(56,189,248,0.14)",
    text: "#e0f2fe",
  },
  file: {
    border: "#34d399",
    fill: "rgba(52,211,153,0.14)",
    text: "#d1fae5",
  },
  keyword: {
    border: "#c084fc",
    fill: "rgba(192,132,252,0.14)",
    text: "#f3e8ff",
  },
  default: {
    border: "#94a3b8",
    fill: "rgba(148,163,184,0.12)",
    text: "#e2e8f0",
  },
};

function shortenSummary(value) {
  if (!value) {
    return "";
  }

  return String(value).replace(/\s+/g, " ").trim().slice(0, 190);
}

function buildNodeLabel(node) {
  const kind = String(node.data?.kind || "node").toUpperCase();
  return `${kind}\n${node.data?.label || node.id}`;
}

function buildElements(sourceNodes, sourceEdges) {
  const nodes = sourceNodes.map((node) => {
    const kind = node.data?.kind || "default";
    const theme = KIND_THEME[kind] || KIND_THEME.default;
    const summary = shortenSummary(node.data?.summary);

    return {
      data: {
        id: node.id,
        label: buildNodeLabel(node),
        rawLabel: node.data?.label || node.id,
        kind,
        category: node.data?.category || "",
        summary,
        source_file: node.data?.source_file || "",
        embedding_id: node.data?.embedding_id || "",
        embedding_path: node.data?.embedding_path || "",
        keyword_count: node.data?.keyword_count || 0,
        document_count: node.data?.document_count || 0,
        borderColor: theme.border,
        fillColor: theme.fill,
        textColor: theme.text,
        width: kind === "document" ? 280 : kind === "category" ? 220 : 240,
        height: kind === "document" ? 170 : 92,
      },
      classes: kind,
    };
  });

  const edges = sourceEdges.map((edge) => {
    const relation = edge.data?.relation || "related";
    const isPrimary = relation === "related documents";

    return {
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        relation,
        label: isPrimary ? edge.label || relation : "",
        inspectorLabel: edge.label || relation,
        weight: Number(edge.data?.weight || 1),
        shared_concepts: edge.data?.shared_concepts || [],
        shared_keywords: edge.data?.shared_keywords || [],
        same_category: Boolean(edge.data?.same_category),
      },
      classes: isPrimary ? "edge-primary" : `edge-${relation.replace(/\s+/g, "-")}`,
    };
  });

  return [...nodes, ...edges];
}

function describeSelection(elementData, isNode) {
  if (!elementData) {
    return {
      title: "Explore the graph",
      body: "Select a node to inspect document metadata, or pick an edge to see why two items were connected.",
    };
  }

  if (isNode) {
    const details = [
      elementData.summary,
      elementData.source_file ? `Source: ${elementData.source_file}` : "",
      elementData.embedding_id ? `Embedding: ${elementData.embedding_id}` : "",
      elementData.document_count ? `Shared by ${elementData.document_count} documents` : "",
      elementData.keyword_count ? `Keywords: ${elementData.keyword_count}` : "",
    ].filter(Boolean);

    return {
      title: elementData.rawLabel,
      body: details.join("  "),
    };
  }

  const bits = [];
  if (elementData.shared_concepts?.length) {
    bits.push(`Shared concepts: ${elementData.shared_concepts.join(", ")}`);
  }
  if (elementData.shared_keywords?.length) {
    bits.push(`Shared keywords: ${elementData.shared_keywords.join(", ")}`);
  }
  if (elementData.same_category) {
    bits.push("Same category");
  }

  return {
    title: elementData.inspectorLabel || elementData.relation,
    body: bits.join("  ") || "This edge captures a semantic relationship in the graph.",
  };
}

export default function GraphPanel({ refreshKey = "" }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [status, setStatus] = useState("Loading graph...");
  const [graphMeta, setGraphMeta] = useState(null);
  const [selection, setSelection] = useState(() => describeSelection(null, true));
  const [isLoading, setIsLoading] = useState(true);
  const [cyElements, setCyElements] = useState([]);

  useEffect(() => {
    let ignore = false;

    const loadGraph = async () => {
      if (!ignore) {
        setIsLoading(true);
      }

      try {
        const payload = await requestJson("/knowledge-graph");

        if (ignore) {
          return;
        }

        const elements = buildElements(payload.nodes || [], payload.edges || []);
        setCyElements(elements);

        startTransition(() => {
          setGraphMeta(payload.meta || null);
          setSelection(describeSelection(null, true));
        });

        setStatus(
          payload.meta?.document_count
            ? `Loaded ${payload.meta.document_count} indexed document${payload.meta.document_count === 1 ? "" : "s"} from Agents/graph.json.`
            : "No knowledge graph data is available yet."
        );
      } catch (error) {
        if (!ignore) {
          setGraphMeta(null);
          setSelection(describeSelection(null, true));
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
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [refreshKey]);

  useEffect(() => {
    if (isLoading) {
      return undefined;
    }

    if (cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
    }

    if (!containerRef.current || cyElements.length === 0) {
      return undefined;
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements: cyElements,
      wheelSensitivity: 0.16,
      pixelRatio: "auto",
      textureOnViewport: false,
      motionBlur: false,
      selectionType: "single",
      style: [
        {
          selector: "node",
          style: {
            shape: "round-rectangle",
            width: "data(width)",
            height: "data(height)",
            padding: "18px",
            "background-color": "data(fillColor)",
            "border-width": 2,
            "border-color": "data(borderColor)",
            label: "data(label)",
            "text-wrap": "wrap",
            "text-max-width": 220,
            "text-valign": "top",
            "text-halign": "left",
            "font-size": 12,
            "font-weight": 650,
            "font-family": "ui-sans-serif, system-ui, sans-serif",
            color: "data(textColor)",
            "text-margin-x": -92,
            "text-margin-y": -26,
            "overlay-opacity": 0,
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-width": 3,
            "border-color": "#f8fafc",
            "shadow-blur": 22,
            "shadow-color": "#f8fafc",
            "shadow-opacity": 0.18,
          },
        },
        {
          selector: "edge",
          style: {
            width: "mapData(weight, 1, 8, 1.5, 4.5)",
            "line-color": "rgba(148,163,184,0.62)",
            "target-arrow-color": "rgba(148,163,184,0.82)",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            "source-endpoint": "outside-to-node",
            "target-endpoint": "outside-to-node",
            "arrow-scale": 1.1,
            "overlay-opacity": 0,
            opacity: 0.9,
          },
        },
        {
          selector: ".edge-primary",
          style: {
            "line-color": "#38bdf8",
            "target-arrow-color": "#38bdf8",
            width: 4.2,
            "z-index": 12,
          },
        },
        {
          selector: ".edge-contextual-proximity",
          style: {
            "line-style": "dashed",
            "line-dash-pattern": [7, 5],
            "line-color": "rgba(192,132,252,0.68)",
            "target-arrow-color": "rgba(192,132,252,0.72)",
            opacity: 0.78,
          },
        },
        {
          selector: ".edge-derived-concept",
          style: {
            "line-color": "rgba(251,146,60,0.72)",
            "target-arrow-color": "rgba(251,146,60,0.76)",
          },
        },
        {
          selector: "edge:selected",
          style: {
            width: 5.2,
            "line-color": "#f8fafc",
            "target-arrow-color": "#f8fafc",
          },
        },
      ],
      layout: {
        name: "dagre",
        rankDir: "LR",
        fit: true,
        padding: 48,
        nodeSep: 60,
        edgeSep: 26,
        rankSep: 180,
        ranker: "network-simplex",
        animate: false,
      },
    });

    cy.on("tap", "node", (event) => {
      setSelection(describeSelection(event.target.data(), true));
    });

    cy.on("tap", "edge", (event) => {
      setSelection(describeSelection(event.target.data(), false));
    });

    cy.on("tap", (event) => {
      if (event.target === cy) {
        setSelection(describeSelection(null, true));
      }
    });

    cy.minZoom(0.35);
    cy.maxZoom(2.2);
    cy.fit(cy.elements(), 40);
    cyRef.current = cy;

    return () => {
      if (cyRef.current === cy) {
        cy.destroy();
        cyRef.current = null;
      }
    };
  }, [cyElements, isLoading]);

  const handleZoom = (direction) => {
    const cy = cyRef.current;
    if (!cy) {
      return;
    }

    const nextLevel = direction === "in" ? cy.zoom() * 1.33 : cy.zoom() * 0.75;
    cy.zoom(nextLevel);
    cy.center(cy.elements());
  };

  const handleZoomIn = () => handleZoom("in");
  const handleZoomOut = () => handleZoom("out");

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

          <div className="flex flex-col items-start gap-3 sm:items-end">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleZoomOut}
                className="inline-flex h-9 items-center justify-center rounded-full border border-white/10 bg-white/5 px-3 text-sm font-semibold text-slate-200 transition hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-cyan-300/60"
              >
                − Zoom out
              </button>
              <button
                type="button"
                onClick={handleZoomIn}
                className="inline-flex h-9 items-center justify-center rounded-full border border-white/10 bg-white/5 px-3 text-sm font-semibold text-slate-200 transition hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-cyan-300/60"
              >
                + Zoom in
              </button>
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
      </div>

      <div className="flex min-h-0 flex-1 flex-col">
        {isLoading ? (
          <div className="flex flex-1 items-center justify-center px-6 py-8 text-center text-xl font-medium text-slate-400">
            Loading data...
          </div>
        ) : (
          <>
            <div className="min-h-0 flex-1">
              <div
                ref={containerRef}
                className="h-[clamp(460px,60vh,820px)] w-full min-w-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.08),_transparent_34%),linear-gradient(180deg,_rgba(2,6,23,0.25),_rgba(2,6,23,0.55))]"
              />
            </div>

            <aside className="border-t border-white/8 bg-slate-950/45 px-5 py-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-cyan-300/70">
                Inspector
              </p>
              <h3 className="mt-3 text-lg font-semibold text-white">{selection.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-300">{selection.body}</p>
            </aside>
          </>
        )}
      </div>
    </section>
  );
}
