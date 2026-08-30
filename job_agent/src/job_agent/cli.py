from __future__ import annotations

import argparse
from pathlib import Path

from .orchestrator import run


def main() -> None:
    parser = argparse.ArgumentParser(prog="job_agent", description="Search, tailor, and apply to jobs.")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Run one full search -> generate -> apply cycle.")
    run_parser.add_argument(
        "--config", default=str(Path(__file__).resolve().parent.parent.parent / "config" / "config.yaml"),
        help="Path to config.yaml",
    )

    args = parser.parse_args()

    if args.command == "run":
        records = run(args.config)
        if not records:
            print("No new matching jobs found this run.")
            return
        print(f"Processed {len(records)} job(s):")
        for r in records:
            print(f"  [{r.status:9s}] {r.job.company} - {r.job.title} ({r.job.source}) :: {r.detail}")


if __name__ == "__main__":
    main()
