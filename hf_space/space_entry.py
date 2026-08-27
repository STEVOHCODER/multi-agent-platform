import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"MailPilot watcher alive")

    def log_message(self, *args):
        pass


def _serve_health():
    port = int(os.environ.get("PORT", 7860))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


threading.Thread(target=_serve_health, daemon=True).start()

import main

main.main(["watch"])
