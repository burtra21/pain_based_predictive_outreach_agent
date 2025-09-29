from __future__ import annotations
from datetime import datetime, timedelta
import math
from typing import List, Dict

EDP_TYPES = [
    "certificate_expiration",
    "detention_risk",
    "crew_poaching_rate",
    "retirement_cliff",
    "contract_at_risk",
    "revenue_loss",
]

def edp_score(urgency: float, meas: float, action: float, univer: float, defens: float) -> float:
    """Weighted EDP score per spec."""
    return 0.4*urgency + 0.2*meas + 0.2*action + 0.1*univer + 0.1*defens

def select_top_edp(candidates: List[Dict]) -> Dict:
    """Pick the highest-scoring EDP candidate."""
    if not candidates:
        return {"edp_type": None, "edp_score": 0.0, "confidence": 0.0, "justification": "No signals"}
    best = max(candidates, key=lambda x: x.get("edp_score", 0))
    return best
