"""Railway entry point.

Runs a lightweight FastAPI health-check server (so the platform has a live
HTTP port to bind/monitor) while the real MailPilot agent
(`EmailWhatsAppAgent`, defined in `agent/agent.py` and driven by `main.py`)
runs continuously in the background via `agent.watch()`.

This replaces the old `minimal_app.py` demo, which was never the real
application entry point.
"""

import logging
import os
import threading

from fastapi import FastAPI

from main import main as run_agent_cli

logger = logging.getLogger("mailpilot.entry")

app = FastAPI()


@app.get("/api/health")
def health():
    return {"status": "ok"}


def _run_agent_watch():
    """Run the MailPilot agent forever (agent.watch()) in a background thread."""
    try:
        run_agent_cli(["watch"])
    except SystemExit:
        # Raised by main.py when required configuration is missing.
        logger.error("Agent did not start: missing configuration (see logs above).")
    except Exception:
        logger.exception("Agent watch loop crashed")


threading.Thread(target=_run_agent_watch, daemon=True).start()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 5300))
    uvicorn.run(app, host="0.0.0.0", port=port)
