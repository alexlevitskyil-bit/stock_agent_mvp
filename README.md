# Stock Agent MVP

Compact Streamlit stock-agent dashboard with separate Investor Mode and Trading Mode, live-first data providers, portfolio health, Plotly drawing charts, an editable watchlist, paper portfolio tracking, and a learning-log approval workflow.

## What is live vs fallback

Live provider priority:

1. **Yahoo Finance via yfinance** for market quotes, OHLCV, profile, fundamentals, Yahoo news, and earnings fields where available.
2. **SEC EDGAR** for latest 10-K, 10-Q, 8-K and official company-facts URL. SEC is disabled unless `SEC_USER_AGENT` is set.
3. **Finnhub** for optional company news and earnings calendar when `FINNHUB_API_KEY` is set.
4. **Mock fallback** only when live providers fail. Mock fallback keeps the app from crashing and labels unavailable market facts as `Data unavailable` or `Mock fallback only`.

The app does not invent financial data. If a provider cannot return a fact, the UI shows `Data unavailable` and stores source/status metadata in `data/sources.json` or the table `sources` field.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```bash
FINNHUB_API_KEY=
SEC_USER_AGENT="stock-agent your_email@example.com"
```

SEC requires a real user-agent value. If it is missing, SEC lookups are disabled and the app reports that status.

## Run

```bash
streamlit run app.py
```

## Dashboard features

- Top Portfolio Health Overview with investor summary, trading summary, main risk, best setup, weakest setup, cash status, and Learning Log access.
- Three-column layout:
  - Left: compact agent summary, hidden full analysis, paper portfolio, learning log.
  - Center: up to three Plotly charts with 5m/15m/1h/1d/1wk timeframe, candle/line view, SMA overlays, and drawing/erase tools.
  - Right: editable manual watchlist columns plus auto-filled calculated columns.
- Agent scan only records decisions for rows where `use_by_agent = true`.
- No real trading execution.
- Learning proposals require explicit approve/reject; code and rules are not changed automatically.

## Data files

- `data/watchlist.csv` — editable manual watchlist inputs.
- `data/sources.json` — source records with source name/link/timestamp.
- `data/agent_portfolio.csv` — paper positions.
- `data/agent_decisions.csv` — stored decision snapshots.
- `data/agent_reviews.csv` — review records.
- `data/learning_log.json` — learning proposals and approval status.
- `data/suggested_stocks.csv` — suggested stock idea records.

## Accuracy note

This is a decision-support MVP, not investment advice. It does not claim full accuracy. Provider fields can be stale, missing, delayed, or unavailable depending on source/API behavior.
