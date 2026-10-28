export const SITE = (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").replace(/\/$/, "");

export const embedCode = (slug: string) => `<script src="${SITE}/embed.js" data-waitlist="${slug}" async></script>`;
export const badgeCode = (slug: string) =>
  `<a href="${SITE}/r/${slug}"><img src="${SITE}/badge/${slug}.svg" alt="Proof of Demand verified signups"></a>`;
