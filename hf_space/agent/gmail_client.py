import base64
import json
import secrets
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from agent.email_client import EmailMessage, parse_raw_message

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
REDIRECT_HOST = "127.0.0.1"


class _LoopbackHandler(BaseHTTPRequestHandler):
    auth_code = None
    error = None

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            _LoopbackHandler.auth_code = query["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>MailPilot authorized. You can close this tab and return to the terminal.</h2>")
        elif "error" in query:
            _LoopbackHandler.error = query["error"][0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"<h2>Authorization failed: {query['error'][0]}</h2>".encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


class GmailClient:
    def __init__(self, client_id, client_secret, token_path):
        if not client_id or not client_secret:
            raise RuntimeError(
                "Gmail API needs GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env "
                "(Google Cloud Console -> Credentials -> OAuth client ID -> Desktop app)"
            )
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_path = Path(token_path)
        self.access_token = ""
        self.refresh_token = ""
        self.expires_at = 0.0
        self._load_token()
        self.session = requests.Session()

    def _load_token(self):
        if not self.token_path.exists():
            return
        try:
            data = json.loads(self.token_path.read_text(encoding="utf-8"))
            self.access_token = data.get("access_token", "")
            self.refresh_token = data.get("refresh_token", "")
            self.expires_at = float(data.get("expires_at", 0))
        except (json.JSONDecodeError, OSError, ValueError):
            pass

    def _save_token(self):
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps({
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
        }, indent=2), encoding="utf-8")

    def authorize(self):
        server = HTTPServer((REDIRECT_HOST, 0), _LoopbackHandler)
        port = server.server_address[1]
        redirect_uri = f"http://{REDIRECT_HOST}:{port}"
        state = secrets.token_urlsafe(16)
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        url = f"{AUTH_URL}?{urlencode(params)}"
        print("\nGmail authorization needed.")
        print(f"1. A browser window is opening ({url[:70]}...)")
        print("2. Sign in to mayintake351@gmail.com and click Allow.")
        print(f"3. Google redirects to {REDIRECT_HOST}:{port} - keep this terminal running.\n")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        webbrowser.open(url)
        deadline = time.time() + 300
        while time.time() < deadline:
            if _LoopbackHandler.auth_code or _LoopbackHandler.error:
                break
            time.sleep(0.5)
        server.shutdown()
        if _LoopbackHandler.error or not _LoopbackHandler.auth_code:
            raise RuntimeError(f"OAuth failed: {_LoopbackHandler.error or 'timed out after 5 minutes'}")
        code = _LoopbackHandler.auth_code
        resp = self.session.post(TOKEN_URL, data={
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }, timeout=20)
        resp.raise_for_status()
        token_data = resp.json()
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token", self.refresh_token)
        self.expires_at = time.time() + int(token_data.get("expires_in", 3600)) - 60
        self._save_token()
        print("Gmail authorized. Token saved to", self.token_path)

    def _ensure_token(self):
        if self.access_token and time.time() < self.expires_at:
            return
        if not self.refresh_token:
            raise RuntimeError("No refresh token; run 'python main.py auth-gmail' first")
        resp = self.session.post(TOKEN_URL, data={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data["access_token"]
        self.expires_at = time.time() + int(data.get("expires_in", 3600)) - 60
        self._save_token()

    def _get(self, path, params=None):
        self._ensure_token()
        resp = self.session.get(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params=params,
            timeout=30,
        )
        if resp.status_code == 401:
            self.access_token = ""
            self._ensure_token()
            resp = self.session.get(
                f"{API_BASE}{path}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params=params,
                timeout=30,
            )
        resp.raise_for_status()
        return resp.json()

    def fetch_since(self, since, batch_size=25):
        days = max(1, (datetime.now(timezone.utc) - since).days + 1)
        query = f"in:anywhere newer_than:{min(days, 7)}d"
        listing = self._get("/messages", {"q": query, "maxResults": min(batch_size, 50)})
        ids = [item["id"] for item in listing.get("messages", [])][:batch_size]
        messages = []
        for message_id in ids:
            detail = self._get(f"/messages/{message_id}", {"format": "raw"})
            raw_bytes = base64.urlsafe_b64decode(detail["raw"] + "===")
            parsed = parse_raw_message(message_id, raw_bytes)
            if parsed.date is None or parsed.date >= since:
                messages.append(parsed)
        return messages
