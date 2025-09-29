"""USCG API client (stub).
Replace endpoints with your paid/approved sources.
"""
import typing as t

class USCGClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def fetch_inspections(self, imo_number: str) -> list[dict]:
        """Return recent USCG/PSC inspection records for a vessel (stub)."""
        return []

    def fetch_company_vessels(self, company_name: str | None = None, domain: str | None = None) -> list[dict]:
        """Return known vessels for an operator (stub)."""
        return []
