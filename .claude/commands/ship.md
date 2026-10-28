---
description: Check, commit and push a finished stage, e.g. /ship A4
---
1. Run my folder's checks (backend: `pytest -q`; web: `npm run build && npm run lint`). Stop if they fail.
2. Show `git status` and `git diff --stat`. Stage ONLY my folder and my prefixed contracts/ files. Never stage .env files.
3. Commit with a message starting "$ARGUMENTS: " that says what the stage does.
4. Run `git pull --rebase origin main`. If anything came in, re-run the checks.
5. Run `git push origin main` (I'll approve it).
