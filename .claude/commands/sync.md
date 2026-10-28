---
description: Safely get my teammate's latest changes
---
1. Run `git status`. If there are uncommitted changes outside my own folder, stop and tell me.
2. Run `git pull --rebase origin main`.
3. Run `git log --oneline -10` and summarize what my teammate changed, especially anything in contracts/.
4. If contracts/ changed, list what in my folder may need updating. Don't change anything yet.
