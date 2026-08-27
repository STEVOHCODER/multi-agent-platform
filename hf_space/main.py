import argparse
import sys
from pathlib import Path

from agent.agent import EmailWhatsAppAgent, setup_logging
from agent.settings import load_settings

ROOT = Path(__file__).resolve().parent


def _build_agent(args):
    settings = load_settings(getattr(args, "config", None))
    setup_logging(
        log_file=settings.agent.log_file,
        level="DEBUG" if getattr(args, "verbose", False) else settings.agent.log_level,
    )
    dry_run = getattr(args, "dry_run", False)
    if not dry_run:
        problems = settings.missing_requirements()
        if problems:
            print("Configuration is incomplete:")
            for p in problems:
                print(f"  - {p}")
            print("\nCopy .env.example to .env and fill in your credentials.")
            print("Run with --dry-run to test without sending WhatsApp messages.")
            sys.exit(1)
    return EmailWhatsAppAgent(settings, dry_run=dry_run)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="mailpilot",
        description="MailPilot: autonomous email reader that forwards important messages to WhatsApp",
    )
    parser.add_argument("--config", default=str(ROOT / "config.yaml"), help="path to config.yaml")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="run a single check cycle")
    run_p.add_argument("--dry-run", action="store_true", help="classify but do not send WhatsApp messages")

    watch_p = sub.add_parser("watch", help="run continuously on an interval")
    watch_p.add_argument("--dry-run", action="store_true", help="classify but do not send WhatsApp messages")

    sub.add_parser("auth-gmail", help="one-time Google OAuth consent for Gmail API access")

    sub.add_parser("status", help="show processed/forwarded stats and recent activity")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "status":
        agent = _build_agent(args)
        agent.status()
        return

    if args.command == "auth-gmail":
        settings = load_settings(args.config)
        if not settings.gmail_client_id or not settings.gmail_client_secret:
            print("Add GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET to .env first")
            print("(Google Cloud Console -> APIs & Services -> Credentials -> Create OAuth client ID -> Desktop app)")
            sys.exit(1)
        from agent.gmail_client import GmailClient
        GmailClient(settings.gmail_client_id, settings.gmail_client_secret, ROOT / "gmail_token.json").authorize()
        return

    agent = _build_agent(args)
    try:
        if args.command == "run":
            report = agent.run_cycle()
            print(f"\nDone. {report.summary()}")
        elif args.command == "watch":
            agent.watch()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
