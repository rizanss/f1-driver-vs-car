"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D, { type ForceGraphMethods, type LinkObject, type NodeObject } from "react-force-graph-2d";
import { THEME } from "@/lib/theme";
import type { Network, Person } from "@/lib/types";

type Node = NodeObject<{ id: string; team: boolean; color: string; mover: boolean }>;
type Link = LinkObject<Node, { seasons: number[]; color: string }>;

const endId = (end: Link["source"]) => (typeof end === "object" ? (end as Node).id : String(end));
const radius = (n: Node, scale: number) => (n.team ? 15 : 10) / scale;

export function NetworkGraph({
  network,
  people,
  selected,
  onSelect,
}: {
  network: Network;
  people: Record<string, Person>;
  selected: string | null;
  onSelect: (id: string | null) => void;
}) {
  const box = useRef<HTMLDivElement>(null);
  const graph = useRef<ForceGraphMethods<Node, Link>>(undefined);
  const images = useRef(new Map<string, HTMLImageElement>());
  const font = useRef("sans-serif");
  const fitted = useRef(false);
  const [width, setWidth] = useState(0);
  const [hover, setHover] = useState<string | null>(null);
  const ready = width > 0;

  const { data, neighbours } = useMemo(() => {
    const color = Object.fromEntries(network.teams.map((t) => [t.id, t.color]));
    const neighbours = new Map<string, Set<string>>();
    for (const l of network.links) {
      neighbours.set(l.source, (neighbours.get(l.source) ?? new Set()).add(l.target));
      neighbours.set(l.target, (neighbours.get(l.target) ?? new Set()).add(l.source));
    }
    const latest = (driver: string) =>
      network.links.filter((l) => l.source === driver).sort((a, b) => b.seasons.at(-1)! - a.seasons.at(-1)!)[0].target;
    const nodes: Node[] = [
      ...network.teams.map((t) => ({ id: t.id, team: true, color: t.color, mover: false })),
      ...network.drivers.map((d) => ({
        id: d.id,
        team: false,
        color: color[latest(d.id)],
        mover: neighbours.get(d.id)!.size > 1,
      })),
    ];
    const links: Link[] = network.links.map((l) => ({ ...l, color: color[l.target] }));
    return { data: { nodes, links }, neighbours };
  }, [network]);

  useEffect(() => {
    font.current = getComputedStyle(document.body).fontFamily;
    for (const [code, person] of Object.entries(people)) {
      if (!person.headshot || images.current.has(code)) continue;
      const img = new Image();
      img.src = person.headshot;
      images.current.set(code, img);
    }
  }, [people]);

  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(box.current!);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const fg = graph.current;
    if (!ready || !fg) return;
    fg.d3Force("charge")?.strength(-150);
    fg.d3Force("link")?.distance((l: Link) => ((l.source as Node).mover ? 45 : 64));
    fg.d3ReheatSimulation();
  }, [ready]);

  const focus = hover ?? selected;
  const near = (id: string) => !focus || id === focus || neighbours.get(focus)!.has(id);
  const height = Math.min(680, Math.max(460, width * 0.8));

  return (
    <div ref={box} className="w-full" style={{ height }}>
      {ready && (
        <ForceGraph2D<Node, Link>
          ref={graph}
          width={width}
          height={height}
          graphData={data}
          backgroundColor="rgba(0,0,0,0)"
          warmupTicks={40}
          cooldownTicks={120}
          enableZoomInteraction={false}
          enablePanInteraction={false}
          onEngineStop={() => {
            if (fitted.current) return;
            fitted.current = true;
            graph.current?.zoomToFit(600, 24);
          }}
          onNodeHover={(n) => setHover(n?.id ?? null)}
          onNodeClick={(n) => onSelect(n.id === selected ? null : n.id)}
          onBackgroundClick={() => onSelect(null)}
          linkColor={(l) => {
            const on = !focus || endId(l.source) === focus || endId(l.target) === focus;
            return `${l.color}${on ? "b3" : "1a"}`;
          }}
          linkWidth={(l) => 0.5 + 0.5 * l.seasons.length}
          nodePointerAreaPaint={(n, paint, ctx, scale) => {
            ctx.fillStyle = paint;
            ctx.beginPath();
            ctx.arc(n.x!, n.y!, radius(n, scale) + 3 / scale, 0, 2 * Math.PI);
            ctx.fill();
          }}
          nodeCanvasObject={(n, ctx, scale) => {
            const r = radius(n, scale);
            const [x, y] = [n.x!, n.y!];
            ctx.globalAlpha = near(n.id) ? 1 : 0.15;
            ctx.beginPath();
            ctx.arc(x, y, r, 0, 2 * Math.PI);
            ctx.fillStyle = n.color;
            ctx.fill();
            const img = images.current.get(n.id);
            if (img?.complete && img.naturalWidth) {
              ctx.save();
              ctx.clip();
              ctx.drawImage(img, x - r, y - r, 2 * r, 2 * r);
              ctx.restore();
            }
            if (n.mover || n.id === focus) {
              ctx.lineWidth = (n.id === focus ? 2 : 1.2) / scale;
              ctx.strokeStyle = n.id === focus ? "#ffffff" : THEME.ink2;
              ctx.stroke();
            }
            const size = (n.team ? 11 : 9) / scale;
            ctx.font = `${n.team ? 700 : 600} ${size}px ${font.current}`;
            ctx.textAlign = "center";
            ctx.textBaseline = "top";
            const text = n.team ? n.id.toUpperCase() : n.id;
            ctx.lineWidth = 3 / scale;
            ctx.strokeStyle = THEME.surface;
            ctx.strokeText(text, x, y + r + 2 / scale);
            ctx.fillStyle = n.team ? "#ffffff" : THEME.ink2;
            ctx.fillText(text, x, y + r + 2 / scale);
            ctx.globalAlpha = 1;
          }}
        />
      )}
    </div>
  );
}
