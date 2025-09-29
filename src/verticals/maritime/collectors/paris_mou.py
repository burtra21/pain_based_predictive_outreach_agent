"""Paris MOU scraping/API client (stub).
See: https://www.parismou.org/ (subject to ToS and legal use).
"""
import typing as t

class ParisMOUClient:
    def __init__(self) -> None:
        pass

    def fetch_recent_detentions(self, operator: str | None = None, imo_number: str | None = None) -> list[dict]:
        return []
