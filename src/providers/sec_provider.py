"""SEC filings provider. Disabled without SEC_USER_AGENT."""
from __future__ import annotations

import os
import requests

from .base import BaseProvider, DATA_UNAVAILABLE, ProviderResult
from .source_registry import make_source

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


class SECProvider(BaseProvider):
    name = "SEC EDGAR"

    def __init__(self) -> None:
        self.user_agent = os.getenv("SEC_USER_AGENT", "").strip().strip('"')
        self.enabled = bool(self.user_agent)

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": self.user_agent}

    def filings(self, ticker: str) -> ProviderResult:
        if not self.enabled:
            return ProviderResult(status=DATA_UNAVAILABLE, error="SEC_USER_AGENT missing; SEC provider disabled")
        try:
            tickers = requests.get(SEC_TICKERS_URL, headers=self._headers(), timeout=15).json()
            cik = None
            for company in tickers.values():
                if company.get("ticker", "").upper() == ticker.upper():
                    cik = str(company.get("cik_str")).zfill(10)
                    break
            if not cik:
                return ProviderResult(error="Ticker not found in SEC company tickers")
            data = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=self._headers(), timeout=15).json()
            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            accessions = recent.get("accessionNumber", [])
            dates = recent.get("filingDate", [])
            rows = []
            for wanted in ["10-K", "10-Q", "8-K"]:
                for idx, form in enumerate(forms):
                    if form == wanted:
                        acc = accessions[idx]
                        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{acc}-index.html"
                        rows.append({"form_type": form, "filing_date": dates[idx], "accession_number": acc, "filing_url": url})
                        break
            return ProviderResult(data={"filings": rows, "official_xbrl_company_facts_url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"}, status="Live" if rows else DATA_UNAVAILABLE, sources=[make_source(self.name, f"https://data.sec.gov/submissions/CIK{cik}.json")])
        except Exception as exc:
            return ProviderResult(error=str(exc))
