"use client";

// Walking crowd, adapted from Skiper UI "Skiper39" (skiper-ui.com, by @gurvinder-singh02),
// itself after codepen.io/zadvorsky/pen/xxwbBQV. Illustrations: Open Peeps (openpeeps.com, CC0).
// ponytail: rAF instead of gsap; the walk is a linear x tween plus a sine bob, no library needed.

import { useEffect, useRef } from "react";

const WALK_SECONDS = 10; // time to cross the stage at speed 1
const BOB_SECONDS = 0.25; // half a bob cycle
const BOB_PX = 10;

type Peep = {
  sx: number; sy: number; w: number; h: number;
  dir: 1 | -1; speed: number; t: number;
  startX: number; endX: number; baseY: number;
};

export function CrowdCanvas({ src, rows = 15, cols = 7, className = "" }: { src: string; rows?: number; cols?: number; className?: string }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const img = new Image();
    let crowd: Peep[] = [];
    let W = 0, H = 0, scale = 1, raf = 0, last = 0;

    const reset = (p: Peep, progress: number) => {
      p.dir = Math.random() > 0.5 ? 1 : -1;
      p.speed = 0.5 + Math.random();
      p.t = progress * WALK_SECONDS;
      const w = p.w * scale, h = p.h * scale;
      p.baseY = H - h + (100 - 250 * Math.random() ** 2) * scale; // most peeps near the bottom edge
      [p.startX, p.endX] = p.dir === 1 ? [-w, W] : [W + w, 0];
    };

    const resize = () => {
      const width = canvas.clientWidth;
      H = canvas.clientHeight;
      canvas.width = width * devicePixelRatio;
      canvas.height = H * devicePixelRatio;
      if (width === W && crowd.length) return; // height-only change (mobile URL bar): keep walking
      W = width;
      scale = Math.max(0.5, Math.min(1, W / 1100));
      crowd.forEach((p) => reset(p, Math.random()));
      crowd.sort((a, b) => a.baseY - b.baseY);
    };

    const draw = () => {
      ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
      ctx.clearRect(0, 0, W, H);
      for (const p of crowd) {
        const k = p.t / WALK_SECONDS;
        const x = p.startX + (p.endX - p.startX) * k;
        const y = p.baseY - BOB_PX * scale * (0.5 - 0.5 * Math.cos((Math.PI * p.t) / BOB_SECONDS));
        ctx.save();
        ctx.translate(x, y);
        ctx.scale(p.dir * scale, scale);
        ctx.drawImage(img, p.sx, p.sy, p.w, p.h, 0, 0, p.w, p.h);
        ctx.restore();
      }
    };

    const tick = (now: number) => {
      const dt = Math.min(0.1, (now - (last || now)) / 1000); // clamp so a background tab doesn't teleport everyone
      last = now;
      let resort = false;
      for (const p of crowd) {
        p.t += dt * p.speed;
        if (p.t >= WALK_SECONDS) { reset(p, 0); resort = true; }
      }
      if (resort) crowd.sort((a, b) => a.baseY - b.baseY);
      draw();
      raf = requestAnimationFrame(tick);
    };

    img.onload = () => {
      const w = img.naturalWidth / rows, h = img.naturalHeight / cols;
      crowd = Array.from({ length: rows * cols }, (_, i) => ({
        sx: (i % rows) * w, sy: Math.floor(i / rows) * h, w, h,
        dir: 1, speed: 1, t: 0, startX: 0, endX: 0, baseY: 0,
      }));
      resize();
      if (reduceMotion) draw();
      else raf = requestAnimationFrame(tick);
    };
    img.src = src;

    const onResize = () => { resize(); if (reduceMotion) draw(); };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      cancelAnimationFrame(raf);
      img.onload = null;
    };
  }, [src, rows, cols]);

  return <canvas ref={ref} aria-hidden className={className} />;
}
