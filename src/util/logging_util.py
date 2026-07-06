"""Append-only JSONL logger for the per-move game trace."""

from __future__ import annotations

import json
from pathlib import Path


class JsonlLogger:
    """Writes one JSON object per line to results/logs/game_log.jsonl."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("w", encoding="utf-8")

    def log(self, record: dict) -> None:
        self._fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "JsonlLogger":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
