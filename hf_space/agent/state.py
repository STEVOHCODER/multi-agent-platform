import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class StateStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._data = {"processed": {}, "history": []}
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self._data["processed"] = loaded.get("processed", {})
                self._data["history"] = loaded.get("history", [])
        except (json.JSONDecodeError, OSError):
            backup = self.path.with_suffix(".corrupt.json")
            try:
                self.path.replace(backup)
            except OSError:
                pass

    def save(self):
        with self._lock:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
            tmp.replace(self.path)

    @staticmethod
    def normalize_message_id(message_id):
        return (message_id or "").strip().strip("<>").lower() or f"uid-{uuid.uuid4()}"

    def seen(self, message_id):
        return self.normalize_message_id(message_id) in self._data["processed"]

    def mark_processed(self, message_id, subject, sender, score, forwarded):
        mid = self.normalize_message_id(message_id)
        with self._lock:
            self._data["processed"][mid] = {
                "subject": (subject or "")[:160],
                "sender": sender,
                "score": score,
                "forwarded": forwarded,
                "at": _now_iso(),
            }
            self._data["history"].append({
                "id": mid,
                "subject": (subject or "")[:160],
                "sender": sender,
                "score": score,
                "forwarded": forwarded,
                "at": _now_iso(),
            })
            self._data["history"] = self._data["history"][-500:]
            if len(self._data["processed"]) > 20000:
                cutoff = sorted(
                    self._data["processed"].items(), key=lambda kv: kv[1].get("at", "")
                )[: len(self._data["processed"]) - 20000]
                for old_id, _ in cutoff:
                    self._data["processed"].pop(old_id, None)

    def stats(self):
        processed = self._data["processed"]
        forwarded = sum(1 for v in processed.values() if v.get("forwarded"))
        last_at = max((v.get("at", "") for v in processed.values()), default="")
        return {
            "total_processed": len(processed),
            "total_forwarded": forwarded,
            "last_activity": last_at,
        }

    def recent(self, limit=15):
        return list(reversed(self._data["history"]))[:limit]
