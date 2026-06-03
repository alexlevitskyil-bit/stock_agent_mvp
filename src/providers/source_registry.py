"""Source capture for external claims."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

DATA_PATH = Path("data/sources.json")


@dataclass
class SourceRecord:
    name: str
    link: str
    timestamp: str
    detail: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_source(name: str, link: str, detail: str = "") -> dict[str, str]:
    return asdict(SourceRecord(name=name, link=link, timestamp=utc_now(), detail=detail))


def save_sources(ticker: str, records: list[dict[str, Any]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DATA_PATH.exists():
        try:
            payload = json.loads(DATA_PATH.read_text())
        except json.JSONDecodeError:
            payload = {}
    else:
        payload = {}
    payload[ticker.upper()] = records
    DATA_PATH.write_text(json.dumps(payload, indent=2))
