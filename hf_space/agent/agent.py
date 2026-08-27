import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from agent.classifier import ImportanceClassifier
from agent.state import StateStore
from agent.whatsapp import WhatsAppSender

ROOT = Path(__file__).resolve().parent.parent
GMAIL_TOKEN_PATH = ROOT / "gmail_token.json"

logger = logging.getLogger("mailpilot")


@dataclass
class CycleReport:
    fetched: int = 0
    evaluated: int = 0
    forwarded: int = 0
    duplicates: int = 0
    below_threshold: int = 0
    errors: list = field(default_factory=list)

    def summary(self):
        parts = [
            f"fetched={self.fetched}",
            f"evaluated={self.evaluated}",
            f"duplicates={self.duplicates}",
            f"below_threshold={self.below_threshold}",
            f"forwarded={self.forwarded}",
        ]
        if self.errors:
            parts.append(f"errors={len(self.errors)}")
        return " ".join(parts)


@dataclass
class ActivityLog:
    entries: deque = field(default_factory=lambda: deque(maxlen=100))

    def add(self, text):
        stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.entries.append(f"[{stamp}] {text}")


def setup_logging(log_file="logs/agent.log", level="INFO"):
    import sys
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(getattr(logging, level, logging.INFO))
    for handler in list(root.handlers):
        root.removeHandler(handler)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S")

    file_handler = RotatingFileHandler(log_path, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(fmt)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    root.addHandler(file_handler)
    root.addHandler(console_handler)


class EmailWhatsAppAgent:
    def __init__(self, settings, dry_run=False):
        self.settings = settings
        self.dry_run = dry_run
        state_path = Path(settings.agent.state_file)
        if not state_path.is_absolute():
            state_path = Path(__file__).resolve().parent.parent / state_path
        self.state = StateStore(state_path)
        self.gemini = None
        if settings.gemini_api_key:
            from agent.gemini import GeminiClient
            self.gemini = GeminiClient(settings.gemini_api_key)
        self.classifier = ImportanceClassifier(
            settings.classifier,
            owner_email=settings.email_address,
            openai_api_key=settings.openai_api_key,
            gemini_client=self.gemini,
        )
        self.sender = None
        if not dry_run:
            self.sender = WhatsAppSender(
                settings.whatsapp,
                token=settings.whatsapp_token,
                twilio_sid=settings.twilio_sid,
                twilio_auth_token=settings.twilio_auth_token,
            )
        self.activity = ActivityLog()
        self._lock_socket = None

    def _resolve_backend(self):
        backend = self.settings.email.backend.lower()
        if backend == "auto":
            has_gmail_oauth = (
                bool(self.settings.gmail_client_id)
                and GMAIL_TOKEN_PATH.exists()
            )
            backend = "gmail_api" if has_gmail_oauth else "imap"
        return backend

    def _fetch_messages(self, since, imap_client=None):
        from agent.email_client import EmailClient
        backend = self._resolve_backend()
        batch = self.settings.email.batch_size
        if backend == "gmail_api":
            from agent.gmail_client import GmailClient
            client = GmailClient(
                self.settings.gmail_client_id,
                self.settings.gmail_client_secret,
                GMAIL_TOKEN_PATH,
            )
            logger.info("Fetching via Gmail API (HTTPS)")
            messages = client.fetch_since(since, batch_size=batch)
        elif backend == "imap":
            client = imap_client or EmailClient(
                host=self.settings.email.host,
                port=self.settings.email.port,
                address=self.settings.email_address,
                password=self.settings.email_password,
                mailbox=self.settings.email.mailbox,
            )
            try:
                if client.mail is None:
                    client.connect()
                messages = client.fetch_since(since, batch_size=batch)
            finally:
                if imap_client is None:
                    client.disconnect()
        else:
            raise RuntimeError(f"unknown email backend '{backend}' (use gmail_api, imap or auto)")
        return messages

    def _summarize(self, msg):
        if not (self.settings.classifier.summarize and self.gemini):
            return None
        summary = self.gemini.summarize(msg)
        if summary:
            logger.info("Gemini summary ready (%d chars)", len(summary))
        return summary

    def run_cycle(self, imap_client=None):
        report = CycleReport()
        since = datetime.now(timezone.utc) - timedelta(hours=self.settings.email.lookback_hours)
        messages = self._fetch_messages(since, imap_client=imap_client)

        report.fetched = len(messages)
        sent_this_cycle = 0
        max_per_cycle = self.settings.agent.max_per_cycle

        for msg in messages:
            if self.state.seen(msg.message_id):
                report.duplicates += 1
                continue
            report.evaluated += 1
            result = self.classifier.classify(msg)
            label = f"{msg.sender_display} | {(msg.subject or '(no subject)')[:60]}"
            if not result.important:
                report.below_threshold += 1
                logger.info("SKIP (%3d) %s", result.score, label)
                self.state.mark_processed(msg.message_id, msg.subject, msg.sender_display, result.score, False)
                continue
            if sent_this_cycle >= max_per_cycle:
                logger.info("HOLD (quota reached) %s", label)
                self.activity.add(f"Held until next cycle: {label}")
                continue
            forwarded_ok = False
            try:
                if self.dry_run:
                    preview = (msg.body_text or "").strip()[:80].replace("\n", " ")
                    logger.info("[DRY-RUN] would forward (%3d): %s | %s...", result.score, label, preview)
                    self.activity.add(f"[dry-run] Would forward: {label}")
                else:
                    summary = self._summarize(msg)
                    self.sender.send_email_alert(msg, result, summary=summary)
                    logger.info("SENT (%3d) %s", result.score, label)
                    self.activity.add(f"Forwarded: {label}")
                forwarded_ok = True
                report.forwarded += 1
                sent_this_cycle += 1
            except Exception as exc:
                report.errors.append(str(exc))
                logger.error("SEND FAILED %s | %s", label, exc)
                self.activity.add(f"Send failed: {label} ({exc})")
            self.state.mark_processed(msg.message_id, msg.subject, msg.sender_display, result.score, forwarded_ok)

        self.state.save()
        logger.info("Cycle complete: %s", report.summary())
        return report

    def _new_imap_client(self):
        from agent.email_client import EmailClient
        return EmailClient(
            host=self.settings.email.host,
            port=self.settings.email.port,
            address=self.settings.email_address,
            password=self.settings.email_password,
            mailbox=self.settings.email.mailbox,
        )

    def _acquire_singleton_lock(self):
        import socket as _socket
        lock = _socket.socket()
        try:
            lock.bind(("127.0.0.1", 47701))
        except OSError:
            logger.error("Another MailPilot watcher is already running on this machine; exiting.")
            raise SystemExit(0)
        lock.listen(0)
        self._lock_socket = lock

    def watch(self):
        self._acquire_singleton_lock()
        if self._resolve_backend() == "imap" and not self.dry_run:
            self.watch_imap_idle()
        else:
            self.watch_polling()

    def watch_imap_idle(self):
        logger.info(
            "Event mode: listening for new mail on %s -> WhatsApp %s (IDLE push, %.0fmin heartbeat)",
            self.settings.email_address,
            self.settings.whatsapp.to_number,
            self.settings.agent.idle_timeout_seconds / 60,
        )
        backoff = 5
        while True:
            client = None
            try:
                client = self._new_imap_client()
                client.connect()
                idle_ok = client.supports_idle()
                logger.info("Connected. IDLE support: %s", idle_ok)
                self.run_cycle(imap_client=client)
                backoff = 5
                while True:
                    got_mail = False
                    try:
                        got_mail = client.idle_wait(timeout=self.settings.agent.idle_timeout_seconds)
                    except ConnectionError as exc:
                        logger.warning("%s; reconnecting", exc)
                        break
                    if got_mail:
                        logger.info("New mail event received - processing now")
                        time.sleep(1)
                        try:
                            self.run_cycle(imap_client=client)
                        except Exception:
                            logger.exception("Cycle failed after IDLE event")
                    else:
                        logger.info("Heartbeat: still listening")
                        try:
                            self.run_cycle(imap_client=client)
                        except Exception:
                            logger.exception("Catch-up cycle failed during heartbeat")
            except KeyboardInterrupt:
                logger.info("Stopped by user.")
                return
            except Exception as exc:
                logger.error("Listener error: %s; retrying in %ss", exc, backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 120)
            finally:
                if client is not None:
                    client.disconnect()

    def watch_polling(self):
        interval = self.settings.agent.interval_seconds
        mode = "DRY-RUN" if self.dry_run else "LIVE"
        logger.info(
            "Polling mode: %s@%s -> WhatsApp %s every %ss [%s]",
            self.settings.email_address,
            self.settings.email.host,
            self.settings.whatsapp.to_number,
            interval,
            mode,
        )
        while True:
            started = time.monotonic()
            try:
                self.run_cycle()
            except KeyboardInterrupt:
                logger.info("Stopped by user.")
                break
            except Exception:
                logger.exception("Cycle crashed; will retry next interval")
            elapsed = time.monotonic() - started
            sleep_for = max(5, interval - elapsed)
            logger.debug("Sleeping %.0fs", sleep_for)
            time.sleep(sleep_for)

    def status(self):
        stats = self.state.stats()
        print("MailPilot agent status")
        print("-" * 40)
        print(f"Mode:        {'DRY-RUN ready' if self.dry_run else 'LIVE'}")
        print(f"Inbox:       {self.settings.email_address or 'NOT SET'} ({self.settings.email.host})")
        print(f"WhatsApp to: {self.settings.whatsapp.to_number or 'NOT SET'} ({self.settings.whatsapp.provider})")
        print(f"AI filter:   {'rules + ' + ('Gemini 2.5 Flash' if self.gemini else 'GPT') if (self.settings.classifier.use_llm and (self.gemini or self.settings.openai_api_key)) else 'rules only'} (min score {self.settings.classifier.min_score})")
        print(f"Summaries:   {'Gemini' if (self.settings.classifier.summarize and self.gemini) else 'off'}")
        print(f"Interval:    event-driven IDLE (heartbeat {self.settings.agent.idle_timeout_seconds}s), max {self.settings.agent.max_per_cycle} alerts/cycle")
        print("-" * 40)
        print(f"Processed:   {stats['total_processed']} emails")
        print(f"Forwarded:   {stats['total_forwarded']} important alerts")
        print(f"Last active: {stats['last_activity'] or 'never'}")
        recent = self.state.recent(10)
        if recent:
            print("\nRecent activity:")
            for item in recent:
                flag = "-> WA" if item.get("forwarded") else "   "
                print(f" {flag} [{item.get('score', '?')}] {(item.get('subject') or '')[:55]} ({item.get('at')})")
