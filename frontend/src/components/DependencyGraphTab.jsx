import { useRef, useEffect, useCallback, useMemo } from "react";
import ForceGraph2D from "react-force-graph-2d";

export default function DependencyGraphTab({ graph }) {
  const graphRef = useRef();

  // Transform the graph data for react-force-graph
  const graphData = useMemo(() => {
    const nodes = (graph.nodes || []).map((n) => ({
      id: n.id,
      label: n.label || n.id,
      // Color based on whether it's a file or a symbol
      color: n.id.includes(".") ? "#6c5ce7" : "#00cec9",
    }));

    const nodeIds = new Set(nodes.map((n) => n.id));

    const links = (graph.edges || []).filter(
      (e) => nodeIds.has(e.from_node) && nodeIds.has(e.to_node)
    ).map((e) => ({
      source: e.from_node,
      target: e.to_node,
      type: e.edge_type,
      color: e.edge_type === "import" ? "rgba(116,185,255,0.5)" : "rgba(253,203,110,0.3)",
    }));

    return { nodes, links };
  }, [graph]);

  // Zoom to fit on initial render
  useEffect(() => {
    if (graphRef.current) {
      setTimeout(() => {
        graphRef.current.zoomToFit(400, 60);
      }, 500);
    }
  }, [graphData]);

  // Custom node painter
  const paintNode = useCallback((node, ctx, globalScale) => {
    const fontSize = Math.max(10 / globalScale, 3);
    const label = node.label || node.id;

    // Node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI);
    ctx.fillStyle = node.color;
    ctx.fill();

    // Glow effect
    ctx.shadowColor = node.color;
    ctx.shadowBlur = 8;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Label
    ctx.font = `${fontSize}px Inter, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#e8e8f0";
    ctx.fillText(label, node.x, node.y + 12);
  }, []);

  return (
    <div className="animate-fade-in-up">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Dependency Graph</h2>
          <p style={{ color: "var(--color-text-secondary)" }}>
            Interactive visualization of imports and function calls across your codebase.
          </p>
        </div>
        <div style={{ display: "flex", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#6c5ce7" }} />
            <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)" }}>Files</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#00cec9" }} />
            <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)" }}>Symbols</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 20, height: 2, background: "rgba(116,185,255,0.7)" }} />
            <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)" }}>Import</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 20, height: 2, background: "rgba(253,203,110,0.7)" }} />
            <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)" }}>Call</span>
          </div>
        </div>
      </div>

      <div
        className="glass-card"
        style={{
          height: "calc(100vh - 220px)",
          borderRadius: 16,
          overflow: "hidden",
          position: "relative",
        }}
      >
        {graphData.nodes.length > 0 ? (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            nodeCanvasObject={paintNode}
            nodePointerAreaPaint={(node, color, ctx) => {
              ctx.beginPath();
              ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI);
              ctx.fillStyle = color;
              ctx.fill();
            }}
            linkColor={(link) => link.color}
            linkWidth={1.5}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            backgroundColor="#0a0a0f"
            cooldownTicks={100}
            d3VelocityDecay={0.3}
          />
        ) : (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--color-text-muted)" }}>
            No dependency data available.
          </div>
        )}
      </div>
    </div>
  );
}
