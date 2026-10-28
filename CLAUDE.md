# Proof of Demand: rules for Claude

- Monorepo: backend/ (Member A, Python FastAPI), web/ (Member B, Next.js), contracts/ (shared).
- Only edit the folder that belongs to the person running this session (see the folder's CLAUDE.md).
  Never edit the other member's folder.
- contracts/: only ADD new files with your prefix (a_ or b_). Never edit existing migration files.
- The API, scoring and event definitions in contracts/ are the source of truth. If code and contract
  disagree, stop and ask instead of changing the contract.
- Never commit secrets. Use .env (gitignored). Add new variable NAMES to contracts/env.example.
- Before finishing a task: run the folder's tests, then `git pull --rebase origin main`.
- Commit messages start with "A" or "B" (e.g. "A4: pain scoring").
- Our plans are in docs/. Use /stage, /sync and /ship (in .claude/commands/) for every stage.

## Contracts (always loaded)
@contracts/api.md
@contracts/scoring.md
@contracts/events.md
