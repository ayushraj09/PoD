---
description: Build one stage from our plan, e.g. /stage A4 or /stage B3
---
Build stage $ARGUMENTS.

1. The letter says whose plan: A → docs/PLAN_A_backend_ml.md, B → docs/PLAN_B_web_payments.md.
   Read section 0 and stage "$ARGUMENTS" of that file. Ignore other stages.
2. Only edit that member's folder (A → backend/, B → web/) and NEW contracts/ files with that prefix.
3. First reply with a short plan (files to create or change, how you'll test it) and wait for my OK.
4. Build it. Write tests or a check command that proves the stage's "Output", and run them.
5. Finish with: what was built, how it was checked, anything I must do by hand
   (keys, running SQL in Supabase, dashboard settings, deploy settings), and a suggested commit message.
