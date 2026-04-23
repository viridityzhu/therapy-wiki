"""Command line entry point."""

import argparse
import sys

from .commands import discuss_command, ingest_command, lint_command, preflight_command, report_command
from .constants import ALL_PERSONAS, DEFAULT_LANGUAGE, DEFAULT_PREFLIGHT_SECONDS, DEFAULT_PROFILE, REPORTABLE_PERSONAS
from .exceptions import TherapyWikiError
from .runtime_log import set_cli_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="therapy", description="Therapy LLM wiki workspace CLI")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress logs on stderr")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Ingest audio or refresh an existing session")
    ingest.add_argument("input", nargs="?", help="Audio file or directory")
    ingest.add_argument("--refresh", help="Rebuild a session from existing artifacts")
    ingest.add_argument("--profile", choices=("fast", "accurate"), default=DEFAULT_PROFILE)
    ingest.add_argument("--language", default=DEFAULT_LANGUAGE)
    ingest.add_argument("--date", help="Override session date (YYYY-MM-DD)")
    ingest.add_argument("--preflight-seconds", type=int, default=DEFAULT_PREFLIGHT_SECONDS)

    preflight = subparsers.add_parser("preflight", help="Run a short STT + diarization smoke test")
    preflight.add_argument("input", help="Audio file or directory")
    preflight.add_argument("--profile", choices=("fast", "accurate"), default=DEFAULT_PROFILE)
    preflight.add_argument("--language", default=DEFAULT_LANGUAGE)
    preflight.add_argument("--seconds", type=int, default=DEFAULT_PREFLIGHT_SECONDS)

    report = subparsers.add_parser("report", help="Build a report packet and draft")
    report.add_argument("scope", choices=("latest", "session", "all"))
    report.add_argument("session_id", nargs="?")
    report.add_argument("--persona", choices=REPORTABLE_PERSONAS, default="therapist")

    discuss = subparsers.add_parser("discuss", help="Build a discussion packet")
    discuss.add_argument("--persona", choices=ALL_PERSONAS, required=True)
    discuss.add_argument("--scope", choices=("latest", "session", "all"), required=True)
    discuss.add_argument("--session-id")
    discuss.add_argument("--question", required=True)
    discuss.add_argument("--file-back", action="store_true")

    lint = subparsers.add_parser("lint", help="Lint the wiki")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    set_cli_logging(not args.quiet)

    try:
        if args.command == "ingest":
            records = ingest_command(
                args.input,
                refresh=args.refresh,
                profile=args.profile,
                language=args.language,
                session_date=args.date,
                preflight_seconds=args.preflight_seconds,
            )
            print("\n".join(record.session_id for record in records) or "No new files ingested.")
            return 0
        if args.command == "preflight":
            print(
                preflight_command(
                    args.input,
                    profile=args.profile,
                    language=args.language,
                    seconds=args.seconds,
                )
            )
            return 0
        if args.command == "report":
            print(report_command(args.scope, persona=args.persona, session_id=args.session_id))
            return 0
        if args.command == "discuss":
            print(
                discuss_command(
                    args.scope,
                    persona=args.persona,
                    question=args.question,
                    session_id=args.session_id,
                    file_back=args.file_back,
                )
            )
            return 0
        if args.command == "lint":
            print(lint_command())
            return 0
    except TherapyWikiError as exc:
        parser.exit(2, f"{exc}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
