import { getReport } from "@/lib/report";

const esc = (s: string) => s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);

// /badge/acme.svg → slug "acme"
export async function GET(_: Request, ctx: RouteContext<"/badge/[slug]">) {
  const slug = (await ctx.params).slug.replace(/\.svg$/, "");
  const r = await getReport(slug).catch(() => null);
  const left = !r ? "not found" : !r.public ? "report private" : `✓ ${r.humans} verified humans · ${r.paid} paid`;
  const right = "Proof of Demand";
  // ponytail: width from char count (~7px/char at 11px), swap for real text metrics if it looks off
  const lw = left.length * 7 + 16;
  const rw = right.length * 7 + 16;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${lw + rw}" height="22" role="img" aria-label="${esc(left)} | ${right}">
<rect width="${lw}" height="22" rx="3" fill="${r?.public ? "#15803d" : "#6b7280"}"/>
<rect x="${lw}" width="${rw}" height="22" rx="3" fill="#111"/>
<rect x="${lw - 3}" width="6" height="22" fill="${r?.public ? "#15803d" : "#6b7280"}"/>
<g fill="#fff" font-family="Verdana,DejaVu Sans,sans-serif" font-size="11">
<text x="8" y="15">${esc(left)}</text><text x="${lw + 8}" y="15">${right}</text>
</g></svg>`;
  return new Response(svg, {
    headers: { "content-type": "image/svg+xml", "cache-control": "public, max-age=300" },
  });
}
