"""Live eval of the pain scorer (needs OPENAI_API_KEY): python -m tests.run_pain_eval"""

import json
from pathlib import Path

from app.pipeline.pain import score_pain


def level(score: int) -> str:
    return "high" if score >= 70 else "medium" if score >= 40 else "low"


def main() -> None:
    rows = [json.loads(line) for line in (Path(__file__).parent / "pain_eval.jsonl").open()]
    hits, manip_ok, normal, manip = 0, 0, 0, 0
    for r in rows:
        out = score_pain(r["transcript"], r["product"], r["question"])
        got = level(out["pain_score"])
        ok = got == r["expected"]
        if r["manipulation"]:
            manip += 1
            manip_ok += ok
        else:
            normal += 1
            hits += ok
        mark = "ok " if ok else "MISS"
        print(f"{mark} {r['expected']:>6} -> {got:<6} {out['pain_score']:>3}  {r['transcript'][:60]}")
        print(f"      reason: {out['pain_reason']}\n      quote:  {out['pain_quote']!r}")
    print(f"\naccuracy: {hits}/{normal} (target >= 16/20)   manipulation scored low: {manip_ok}/{manip}")


if __name__ == "__main__":
    main()
