import React, { useEffect, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

const API = "http://localhost:8000/api";
const LAYOUT_KEY = "linknotes-graph-layout-v1";

const loadLayout = () => {
  try {
    return JSON.parse(localStorage.getItem(LAYOUT_KEY) || "{}");
  } catch {
    return {};
  }
};

const saveLayout = (layout) => {
  try {
    localStorage.setItem(LAYOUT_KEY, JSON.stringify(layout));
  } catch {
    /* quota / disabled — silent fail */
  }
};

const NODE_HEIGHT = 64;
const NODE_PAD_X = 14;
const FONT_TITLE = 13;
const FONT_META = 11;

function getNodeWidth(node) {
  const len = (node.title || "").length;
  return Math.max(140, Math.min(260, len * 7.5 + NODE_PAD_X * 2));
}

function rectEdgePoint(cx, cy, halfW, halfH, fromX, fromY) {
  const dx = fromX - cx;
  const dy = fromY - cy;
  if (dx === 0 && dy === 0) return { x: cx, y: cy };
  const tX = dx !== 0 ? halfW / Math.abs(dx) : Infinity;
  const tY = dy !== 0 ? halfH / Math.abs(dy) : Infinity;
  const t = Math.min(tX, tY);
  return { x: cx + t * dx, y: cy + t * dy };
}

function roundedRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function Graph({ onNodeClick, selectedId }) {
  const [data, setData] = useState({ nodes: [], links: [] });
  const [size, setSize] = useState({ w: 800, h: 600 });
  const wrapRef = useRef(null);
  const fgRef = useRef(null);
  const frozenRef = useRef(false);
  const layoutRef = useRef(loadLayout());

  const fetchGraph = (resetLayout = false) => {
    if (resetLayout) {
      layoutRef.current = {};
      saveLayout({});
    }
    fetch(`${API}/graph`)
      .then((r) => r.json())
      .then((d) => {
        const inDeg = {};
        const outDeg = {};
        d.links.forEach((l) => {
          outDeg[l.source] = (outDeg[l.source] || 0) + 1;
          inDeg[l.target] = (inDeg[l.target] || 0) + 1;
        });
        d.nodes.forEach((n) => {
          n.outDeg = outDeg[n.id] || 0;
          n.inDeg = inDeg[n.id] || 0;
          const saved = layoutRef.current[n.id];
          if (saved) {
            n.x = saved.x;
            n.y = saved.y;
            n.fx = saved.x;
            n.fy = saved.y;
          } else {
            n.fx = undefined;
            n.fy = undefined;
          }
        });
        frozenRef.current = false;
        setData(d);
      });
  };

  useEffect(() => {
    fetchGraph();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!data.nodes.length || !fgRef.current) return;
    const linkF = fgRef.current.d3Force("link");
    if (linkF) linkF.distance(240);
    const chargeF = fgRef.current.d3Force("charge");
    if (chargeF) chargeF.strength(-900);
  }, [data]);

  useEffect(() => {
    if (!wrapRef.current) return;
    const update = () => {
      if (!wrapRef.current) return;
      const r = wrapRef.current.getBoundingClientRect();
      setSize({ w: Math.max(300, r.width), h: Math.max(300, r.height) });
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  const freezeAll = () => {
    const layout = { ...layoutRef.current };
    data.nodes.forEach((n) => {
      n.fx = n.x;
      n.fy = n.y;
      layout[n.id] = { x: n.x, y: n.y };
    });
    layoutRef.current = layout;
    saveLayout(layout);
    frozenRef.current = true;
  };

  const handleEngineStop = () => {
    if (!frozenRef.current) freezeAll();
    fgRef.current?.zoomToFit(400, 80);
  };

  const drawNode = (node, ctx, scale) => {
    const w = getNodeWidth(node);
    const h = NODE_HEIGHT;
    const x = node.x - w / 2;
    const y = node.y - h / 2;
    const isSelected = node.id === selectedId;

    ctx.save();
    ctx.shadowColor = "rgba(0,0,0,0.12)";
    ctx.shadowBlur = 6;
    ctx.shadowOffsetY = 2;
    roundedRect(ctx, x, y, w, h, 8);
    ctx.fillStyle = isSelected ? "#fff5d6" : "#ffffff";
    ctx.fill();
    ctx.restore();

    roundedRect(ctx, x, y, w, h, 8);
    ctx.lineWidth = isSelected ? 2.5 : 1.2;
    ctx.strokeStyle = isSelected ? "#e94560" : "#1a1a2e";
    ctx.stroke();

    ctx.textBaseline = "top";
    ctx.textAlign = "left";

    ctx.font = `bold ${FONT_TITLE}px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`;
    ctx.fillStyle = "#1a1a2e";
    const title = node.title || "";
    const maxTitle = w - NODE_PAD_X * 2;
    let displayTitle = title;
    if (ctx.measureText(title).width > maxTitle) {
      while (
        displayTitle.length > 1 &&
        ctx.measureText(displayTitle + "…").width > maxTitle
      ) {
        displayTitle = displayTitle.slice(0, -1);
      }
      displayTitle += "…";
    }
    ctx.fillText(displayTitle, x + NODE_PAD_X, y + 8);

    ctx.font = `${FONT_META}px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`;
    ctx.fillStyle = "#1d4ed8";
    ctx.fillText(`→ ${node.outDeg} link${node.outDeg === 1 ? "" : "s"}`, x + NODE_PAD_X, y + 28);
    ctx.fillStyle = "#15803d";
    ctx.fillText(
      `← ${node.inDeg} backlink${node.inDeg === 1 ? "" : "s"}`,
      x + NODE_PAD_X,
      y + 44
    );

    node.__w = w;
    node.__h = h;
  };

  const paintHitArea = (node, color, ctx) => {
    const w = node.__w || getNodeWidth(node);
    const h = node.__h || NODE_HEIGHT;
    ctx.fillStyle = color;
    ctx.fillRect(node.x - w / 2, node.y - h / 2, w, h);
  };

  const drawLink = (link, ctx) => {
    const s = link.source;
    const t = link.target;
    if (!s || !t || s.x == null || t.x == null) return;
    const sw = (s.__w || getNodeWidth(s)) / 2;
    const sh = (s.__h || NODE_HEIGHT) / 2;
    const tw = (t.__w || getNodeWidth(t)) / 2;
    const th = (t.__h || NODE_HEIGHT) / 2;

    const sEdge = rectEdgePoint(s.x, s.y, sw, sh, t.x, t.y);
    const tEdge = rectEdgePoint(t.x, t.y, tw, th, s.x, s.y);

    ctx.strokeStyle = "rgba(80,80,110,0.55)";
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(sEdge.x, sEdge.y);
    ctx.lineTo(tEdge.x, tEdge.y);
    ctx.stroke();

    const angle = Math.atan2(tEdge.y - sEdge.y, tEdge.x - sEdge.x);
    const arrow = 9;
    ctx.fillStyle = "rgba(80,80,110,0.85)";
    ctx.beginPath();
    ctx.moveTo(tEdge.x, tEdge.y);
    ctx.lineTo(
      tEdge.x - arrow * Math.cos(angle - Math.PI / 7),
      tEdge.y - arrow * Math.sin(angle - Math.PI / 7)
    );
    ctx.lineTo(
      tEdge.x - arrow * Math.cos(angle + Math.PI / 7),
      tEdge.y - arrow * Math.sin(angle + Math.PI / 7)
    );
    ctx.closePath();
    ctx.fill();
  };

  const handleNodeDragEnd = (node) => {
    node.fx = node.x;
    node.fy = node.y;
    layoutRef.current = {
      ...layoutRef.current,
      [node.id]: { x: node.x, y: node.y },
    };
    saveLayout(layoutRef.current);
  };

  const handleReset = () => {
    fetchGraph(true);
  };

  return (
    <div className="graph-wrap" ref={wrapRef}>
      <button className="graph-reset-btn" onClick={handleReset} title="Re-run auto-layout and forget saved positions">
        Reset layout
      </button>
      {data.nodes.length === 0 ? (
        <div className="empty-state">
          <p>Loading graph...</p>
        </div>
      ) : (
        <ForceGraph2D
          ref={fgRef}
          graphData={data}
          width={size.w}
          height={size.h}
          backgroundColor="#fafafa"
          nodeLabel={(n) =>
            `${n.title} — PageRank ${n.score?.toFixed(3) ?? "0"}`
          }
          nodeCanvasObject={drawNode}
          nodePointerAreaPaint={paintHitArea}
          linkCanvasObject={drawLink}
          linkCanvasObjectMode={() => "replace"}
          onNodeClick={(n) => onNodeClick && onNodeClick(n.id)}
          onNodeDragEnd={handleNodeDragEnd}
          onEngineStop={handleEngineStop}
          cooldownTicks={200}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          enablePanInteraction={true}
        />
      )}
    </div>
  );
}

export default Graph;
