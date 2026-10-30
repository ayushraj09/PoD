"""Set up TigerGraph Savanna for the ring check (stage A8). Needs TG_HOST, TG_GRAPH, TG_SECRET.

    python -m scripts.tg_setup --check    # connect and list the graph, change nothing
    python -m scripts.tg_setup            # add our vertex/edge types, install ring_of
    python -m scripts.tg_setup --query    # (re)install ring_of only
"""

import argparse
from pathlib import Path

from app.config import get_settings
from app.pipeline.graph import _connect

GSQL_DIR = Path(__file__).resolve().parent.parent / "tigergraph"


def gsql_file(name: str, graph: str) -> str:
    text = (GSQL_DIR / name).read_text().replace("GRAPH_NAME", graph)
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//"))


def run(conn, label: str, statement: str) -> str:
    print(f"--- {label}")
    out = conn.gsql(statement)
    print(out if isinstance(out, str) else repr(out))
    return out if isinstance(out, str) else repr(out)


def backfill(slug: str) -> None:
    """Repairs graph writes lost while the workspace was asleep, then re-checks every ring."""
    from app import db
    from app.pipeline.graph import _with_retry, check_ring, write_signup

    wl = db.get_waitlist_by_slug(slug)
    rows = db.client().table("signups").select("*").eq("waitlist_id", wl["id"]) \
        .eq("status", "scored").order("created_at").execute().data
    for r in rows:
        _with_retry(lambda c, row=r: write_signup(c, row))
    for r in rows:
        check_ring(db.get_signup(r["id"]))
    for r in rows:
        r = db.get_signup(r["id"])
        print(f"{r['email'][:28]:28} {r['human_verdict']:>10} trust={r['trust_score']} "
              f"flags={[f['code'] for f in r['flags']]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="connect and list only")
    ap.add_argument("--query", action="store_true", help="only (re)install ring_of")
    ap.add_argument("--backfill", metavar="SLUG", help="re-write a waitlist's signups and re-check rings")
    args = ap.parse_args()
    if args.backfill:
        backfill(args.backfill)
        return

    s = get_settings()
    if not (s.tg_host and s.tg_graph and s.tg_secret):
        raise SystemExit("Set TG_HOST, TG_GRAPH and TG_SECRET in backend/.env first.")
    conn = _connect()
    print(f"connected to {s.tg_host}, graph {s.tg_graph}")

    overview = run(conn, "graphs in this workspace", "ls")
    graph_exists = f"Graph {s.tg_graph}(" in overview
    if args.check:
        if graph_exists:
            run(conn, f"graph {s.tg_graph}", f"USE GRAPH {s.tg_graph}\nls")
        else:
            print(f"--- graph {s.tg_graph} does not exist yet; setup will create it")
        return

    if not graph_exists:
        run(conn, f"create graph {s.tg_graph}", f"CREATE GRAPH {s.tg_graph}()")
    listing = run(conn, "ls", f"USE GRAPH {s.tg_graph}\nls")

    if not args.query:
        if "Signup" in listing:
            print("--- schema: Signup already exists, skipping schema change")
        else:
            run(conn, "schema change", gsql_file("schema.gsql", s.tg_graph))

    query = gsql_file("ring_of.gsql", s.tg_graph)
    if "ring_of" in listing:
        run(conn, "drop old ring_of", f"USE GRAPH {s.tg_graph}\nDROP QUERY ring_of")
    run(conn, "create ring_of", f"USE GRAPH {s.tg_graph}\n{query}")
    run(conn, "install ring_of (takes a minute)", f"USE GRAPH {s.tg_graph}\nINSTALL QUERY ring_of")
    run(conn, "ls after", f"USE GRAPH {s.tg_graph}\nls")


if __name__ == "__main__":
    main()
