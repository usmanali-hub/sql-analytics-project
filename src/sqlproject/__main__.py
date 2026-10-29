"""``python -m sqlproject docs|report|check``: regenerate documentation, run the queries, or check the data."""

import argparse
from pathlib import Path

from .db import DEFAULT_DB, connect, integrity_problems
from .diagram import profile_markdown, schema_markdown
from .runner import ROOT, load_queries, write_outputs


def main() -> int:
    parser = argparse.ArgumentParser(prog="sqlproject")
    parser.add_argument("command", choices=["docs", "report", "check"])
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--out", default="docs")
    args = parser.parse_args()
    conn = connect(args.db)
    if args.command == "check":
        problems = integrity_problems(conn)
        print("database is sound" if not problems else "\n".join(problems))
        return 1 if problems else 0
    if args.command == "report":
        queries = load_queries()
        write_outputs(conn, queries, ROOT / "results", Path(args.out) / "business_questions.md")
        print(f"ran {len(queries)} queries; wrote results/ and {Path(args.out) / 'business_questions.md'}")
        return 0
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "schema.md").write_text(schema_markdown(conn), encoding="utf-8")
    (out / "data_profile.md").write_text(profile_markdown(conn), encoding="utf-8")
    print(f"wrote {out / 'schema.md'} and {out / 'data_profile.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
