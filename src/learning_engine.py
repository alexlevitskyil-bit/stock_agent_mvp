"""Paper portfolio and learning-log approval helpers."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import pandas as pd

STARTING_CAPITAL = 10_000.0
PORTFOLIO_PATH = Path("data/agent_portfolio.csv")
DECISIONS_PATH = Path("data/agent_decisions.csv")
REVIEWS_PATH = Path("data/agent_reviews.csv")
LOG_PATH = Path("data/learning_log.json")

PORTFOLIO_COLUMNS = ["ticker", "mode", "entry_date", "entry_price", "shares", "cost", "current_price", "unrealized_p_l", "realized_p_l", "stop", "target_1", "target_2", "thesis", "decision_reason", "status", "review_notes"]
LOG_FIELDS = ["id", "date", "status", "severity", "confidence", "problem", "evidence", "affected_trades", "old_rule", "new_rule", "proposed_code_change", "affected_files", "expected_improvement", "risk_of_change", "backtest_required", "approved", "applied"]


def ensure_learning_files() -> None:
    Path("data").mkdir(exist_ok=True)
    if not PORTFOLIO_PATH.exists():
        pd.DataFrame(columns=PORTFOLIO_COLUMNS).to_csv(PORTFOLIO_PATH, index=False)
    if not DECISIONS_PATH.exists():
        pd.DataFrame(columns=["timestamp", "ticker", "mode", "decision", "score", "risk_level", "reason", "sources"]).to_csv(DECISIONS_PATH, index=False)
    if not REVIEWS_PATH.exists():
        pd.DataFrame(columns=["timestamp", "ticker", "status", "review_notes"]).to_csv(REVIEWS_PATH, index=False)
    if not LOG_PATH.exists():
        LOG_PATH.write_text("[]")


def load_agent_portfolio() -> pd.DataFrame:
    ensure_learning_files()
    return pd.read_csv(PORTFOLIO_PATH)


def portfolio_summary(df: pd.DataFrame) -> dict:
    cash = STARTING_CAPITAL - pd.to_numeric(df.get("cost", 0), errors="coerce").fillna(0).sum() + pd.to_numeric(df.get("realized_p_l", 0), errors="coerce").fillna(0).sum()
    unrealized = pd.to_numeric(df.get("unrealized_p_l", 0), errors="coerce").fillna(0).sum()
    realized = pd.to_numeric(df.get("realized_p_l", 0), errors="coerce").fillna(0).sum()
    return {"starting_capital": STARTING_CAPITAL, "cash": cash, "realized_p_l": realized, "unrealized_p_l": unrealized}


def record_decision(decision: dict) -> None:
    ensure_learning_files()
    df = pd.read_csv(DECISIONS_PATH)
    row = {"timestamp": datetime.now(timezone.utc).isoformat(), "ticker": decision.get("ticker"), "mode": decision.get("mode"), "decision": decision.get("decision"), "score": decision.get("investor_score"), "risk_level": decision.get("risk_level"), "reason": decision.get("key_reason"), "sources": json.dumps(decision.get("sources", []))}
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DECISIONS_PATH, index=False)


def load_learning_log() -> list[dict]:
    ensure_learning_files()
    try:
        return json.loads(LOG_PATH.read_text())
    except json.JSONDecodeError:
        return []


def save_learning_log(rows: list[dict]) -> None:
    LOG_PATH.write_text(json.dumps(rows, indent=2))


def has_pending_proposals() -> bool:
    return any(row.get("status") == "Proposed" and not row.get("approved") for row in load_learning_log())


def update_proposal_status(proposal_id: str, status: str) -> None:
    rows = load_learning_log()
    for row in rows:
        if row.get("id") == proposal_id:
            row["status"] = status
            row["approved"] = status == "Approved"
    save_learning_log(rows)
