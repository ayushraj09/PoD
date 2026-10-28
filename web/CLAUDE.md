# web/ is owned by Member B
- Next.js App Router + TypeScript + Tailwind. Run: npm run dev. Check: npm run build && npm run lint
- Read contracts/api.md, contracts/scoring.md before touching data or labels.
- Never call the backend from founders' sites directly; the widget is always an iframe of /w/[slug].
- Server-only secrets (service key, Dodo keys) never go in NEXT_PUBLIC_ variables.
