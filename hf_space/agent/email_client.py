import base64
import email
import html as htmllib
import imaplib
import re
import socket
import ssl
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.header import decode_header, make_header
from email.utils import getaddresses, parseaddr, parsedate_to_datetime

DOH_ENDPOINTS = (
    "https://1.1.1.1/dns-query?name={host}&type=A",
    "https://8.8.8.8/resolve?name={host}&type=A",
    "https://cloudflare-dns.com/dns-query?name={host}&type=A",
    "https://dns.google/resolve?name={host}&type=A",
)


def doh_resolve(host):
    try:
        return socket.gethostbyname(host)
    except OSError:
        pass
    try:
        import requests
    except ImportError:
        return None
    for url_template in DOH_ENDPOINTS:
        try:
            resp = requests.get(
                url_template.format(host=host),
                headers={"accept": "application/dns-json"},
                timeout=10,
            )
            answers = [
                entry["data"]
                for entry in resp.json().get("Answer", [])
                if entry.get("type") == 1
            ]
            if answers:
                return answers[0]
        except Exception:
            continue
    return None


def _proxy_url():
    proxies = urllib.request.getproxies()
    return proxies.get("https") or proxies.get("http")


def _connect_via_proxy(target_host, target_port, timeout):
    proxy = _proxy_url()
    if not proxy:
        raise OSError(f"no system proxy configured")
    parsed = urllib.parse.urlparse(proxy if "//" in proxy else f"http://{proxy}")
    sock = socket.create_connection((parsed.hostname, parsed.port or 8080), timeout=timeout)
    headers = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\nHost: {target_host}:{target_port}\r\n"
    if parsed.username:
        import base64 as b64
        credentials = b64.b64encode(f"{urllib.parse.unquote(parsed.username)}:{urllib.parse.unquote(parsed.password or '')}".encode()).decode()
        headers += f"Proxy-Authorization: Basic {credentials}\r\n"
    headers += "\r\n"
    sock.sendall(headers.encode())
    response = b""
    while b"\r\n\r\n" not in response and len(response) < 8192:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    first_line = response.split(b"\r\n", 1)[0]
    if b" 200" not in first_line:
        sock.close()
        raise OSError(f"proxy CONNECT to {target_host}:{target_port} refused: {first_line!r}")
    return sock


def _open_socket_with_fallback(direct_target, port, sni_host, timeout):
    proxy_available = _proxy_url() is not None
    order = [True, False] if proxy_available else [False]
    last_exc = None
    for use_proxy in order:
        try:
            if use_proxy:
                return _connect_via_proxy(sni_host, port, timeout)
            return socket.create_connection((direct_target, port), timeout=timeout)
        except OSError as exc:
            last_exc = exc
    raise last_exc


class _IMAP4SSLWithHostname(imaplib.IMAP4_SSL):
    def __init__(self, address, port, hostname, timeout=30):
        self.sni_hostname = hostname
        self._timeout = timeout
        try:
            super().__init__(address, int(port), timeout=timeout)
        except TypeError:
            super().__init__(address, int(port))

    def _create_socket(self, timeout=None):
        effective_timeout = timeout or self._timeout
        sock = _open_socket_with_fallback(self.host, self.port, self.sni_hostname, effective_timeout)
        return self.ssl_context.wrap_socket(sock, server_hostname=self.sni_hostname)


@dataclass
class EmailMessage:
    uid: str = ""
    message_id: str = ""
    sender_email: str = ""
    sender_name: str = ""
    to_addresses: list = field(default_factory=list)
    subject: str = ""
    body_text: str = ""
    date: object = None
    has_attachments: bool = False
    has_list_unsubscribe: bool = False

    @property
    def sender_display(self):
        return f"{self.sender_name} <{self.sender_email}>" if self.sender_name else self.sender_email


def decode_header_value(value):
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value))).strip()
    except Exception:
        return str(value).strip()


def _html_to_text(html):
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</(p|div|tr|h[1-6]|li)>", "\n\n", html)
    text = re.sub(r"<[^>]+>", " ", html)
    text = htmllib.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def _decode_part(part):
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def _extract_body(msg):
    plain = ""
    html_body = ""
    has_attachments = False
    for part in msg.walk():
        if part.is_multipart():
            continue
        disposition = (part.get_content_disposition() or "").lower()
        filename = part.get_filename()
        if disposition == "attachment" or (filename and disposition != "inline"):
            has_attachments = True
            continue
        ctype = part.get_content_type()
        if ctype == "text/plain" and not plain:
            candidate = _decode_part(part).strip()
            if candidate:
                plain = candidate
        elif ctype == "text/html" and not html_body:
            html_body = _decode_part(part)
    if plain:
        return plain, has_attachments
    if html_body:
        return _html_to_text(html_body), has_attachments
    return "", has_attachments


def parse_raw_message(uid, raw_bytes):
    msg = email.message_from_bytes(raw_bytes)
    message_id = msg.get("Message-ID", "") or f"<generated-{uid}>"
    sender_name, sender_email = parseaddr(decode_header_value(msg.get("From", "")))
    to_pairs = getaddresses([decode_header_value(msg.get("To", ""))])
    to_addresses = [addr.lower() for _, addr in to_pairs if addr]
    subject = decode_header_value(msg.get("Subject", ""))
    body_text, has_attachments = _extract_body(msg)
    received_at = None
    raw_date = msg.get("Date")
    if raw_date:
        try:
            received_at = parsedate_to_datetime(raw_date)
            if received_at.tzinfo is None:
                received_at = received_at.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            received_at = None
    return EmailMessage(
        uid=str(uid),
        message_id=message_id,
        sender_email=(sender_email or "").lower(),
        sender_name=sender_name,
        to_addresses=to_addresses,
        subject=subject,
        body_text=body_text,
        date=received_at,
        has_attachments=has_attachments,
        has_list_unsubscribe=bool(msg.get("List-Unsubscribe")),
    )


class EmailClient:
    def __init__(self, host, port, address, password, mailbox="INBOX"):
        self.host = host
        self.port = int(port)
        self.address = address
        self.password = password
        self.mailbox = mailbox
        self.mail = None

    def connect(self):
        ip = doh_resolve(self.host)
        target = ip or self.host
        self.mail = _IMAP4SSLWithHostname(target, self.port, self.host)
        self.mail.login(self.address, self.password)
        return self.mail

    def disconnect(self):
        if self.mail is not None:
            try:
                self.mail.logout()
            except Exception:
                pass
            self.mail = None

    def fetch_since(self, since, batch_size=25):
        if self.mail is None:
            self.connect()
        status, _ = self.mail.select(self.mailbox, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Could not open mailbox '{self.mailbox}'")
        since_str = since.strftime("%d-%b-%Y")
        status, data = self.mail.uid("search", None, f'(SINCE "{since_str}")')
        if status != "OK":
            raise RuntimeError("IMAP UID search failed")
        uids = data[0].split()
        if len(uids) > batch_size:
            uids = uids[-batch_size:]
        messages = []
        for uid in reversed(uids):
            status, msg_data = self.mail.uid("fetch", uid, "(RFC822)")
            if status != "OK" or not msg_data or msg_data[0] is None:
                continue
            messages.append(parse_raw_message(uid.decode("ascii", errors="replace"), msg_data[0][1]))
        return messages

    def supports_idle(self):
        if self.mail is None:
            self.connect()
        try:
            status, caps = self.mail.capability()
            return status == "OK" and b"IDLE" in (caps[0] or b"").upper()
        except Exception:
            return False

    def idle_wait(self, timeout=300):
        """Block until the server announces new mail (EXISTS) or timeout.

        Returns True when new mail likely arrived, False on timeout/error.
        """
        mail = self.mail
        sock = mail.socket()
        tag = None
        idle_started = False
        original_timeout = sock.gettimeout()
        try:
            sock.settimeout(min(timeout, 60))
            tag = mail._new_tag().decode()
            sock.sendall(f"{tag} IDLE\r\n".encode())
            response = b""
            while b"+" not in response:
                chunk = sock.recv(1024)
                if not chunk:
                    raise ConnectionError("no continuation after IDLE")
                response += chunk
            idle_started = True

            saw_exists = False
            deadline = time.time() + min(timeout, 25 * 60)
            sock.settimeout(15)
            while time.time() < deadline:
                try:
                    data = sock.recv(4096)
                except (socket.timeout, TimeoutError):
                    continue
                if not data:
                    break
                text = data.decode("ascii", errors="replace")
                if "EXISTS" in text:
                    saw_exists = True
                    break
                if f"{tag} " in text:
                    break
            return saw_exists
        except (OSError, ssl.SSLError, imaplib.IMAP4.error) as exc:
            raise ConnectionError(f"IDLE failed: {exc}") from exc
        finally:
            if idle_started and tag is not None:
                try:
                    sock.settimeout(10)
                    sock.sendall(b"DONE\r\n")
                    drain = b""
                    while f"{tag} " not in drain.decode("ascii", errors="replace") and len(drain) < 65536:
                        chunk = sock.recv(4096)
                        if not chunk:
                            break
                        drain += chunk
                except Exception:
                    pass
            try:
                sock.settimeout(original_timeout)
            except Exception:
                pass
