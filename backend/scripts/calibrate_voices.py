"""Calibrate VOICE_MATCH_THRESHOLD on real recordings.

Put recordings in one folder named <person>_<n>.<ext> (e.g. ayush_1.webm, ayush_2.m4a, guest3_1.webm),
then run:  python -m scripts.calibrate_voices recordings/ [--out docs/voice_calibration.md]
"""

import argparse
import itertools
import tempfile
from pathlib import Path

import numpy as np

from app import models
from app.pipeline.audio import clean
from app.pipeline.voice import embed, similarity

EXTS = {".webm", ".mp4", ".m4a", ".ogg", ".wav", ".mp3"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--out", type=Path, default=Path("docs/voice_calibration.md"))
    args = ap.parse_args()

    models.load()
    embs = {}
    for f in sorted(p for p in args.folder.iterdir() if p.suffix.lower() in EXTS):
        with tempfile.TemporaryDirectory() as tmp:
            embs[f.stem] = embed(clean(f, Path(tmp)).wav_path)

    same, diff = [], []
    for (a, ea), (b, eb) in itertools.combinations(embs.items(), 2):
        s = similarity(ea, eb)
        (same if a.split("_")[0] == b.split("_")[0] else diff).append((s, a, b))

    lines = ["# Voice match calibration", "",
             f"{len(embs)} recordings, {len({k.split('_')[0] for k in embs})} people.", ""]
    for name, group in (("Same person", same), ("Different people", diff)):
        vals = [s for s, _, _ in group]
        if vals:
            lines.append(f"**{name}** ({len(vals)} pairs): min {min(vals):.3f}, "
                         f"mean {np.mean(vals):.3f}, max {max(vals):.3f}")
    lines.append("")
    if same and diff:
        lo, hi = max(s for s, _, _ in diff), min(s for s, _, _ in same)
        suggested = round((lo + hi) / 2, 2)
        gap = "clean gap" if hi > lo else "OVERLAP: pick a value that favours fewer false matches"
        lines += [f"Highest different-people score {lo:.3f}, lowest same-person score {hi:.3f} ({gap}).",
                  "", f"**Suggested VOICE_MATCH_THRESHOLD = {suggested}**", ""]
    lines += ["| Pair | Similarity | Same person |", "|---|---|---|"]
    for s, a, b in sorted(same + diff, reverse=True):
        lines.append(f"| {a} vs {b} | {s:.3f} | {'yes' if (s, a, b) in same else 'no'} |")

    text = "\n".join(lines) + "\n"
    print(text)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text)


if __name__ == "__main__":
    main()
