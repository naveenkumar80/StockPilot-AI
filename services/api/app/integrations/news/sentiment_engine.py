import re
from typing import Tuple, List, Optional
from app.integrations.news.base import SentimentAnalysis


# Financial sentiment dictionaries tailored for corporate earnings, market moves & regulatory filings
POSITIVE_TERMS = {
    "surge": 0.8, "surges": 0.8, "surged": 0.8,
    "jump": 0.7, "jumps": 0.7, "jumped": 0.7,
    "profit up": 0.85, "profit surges": 0.9, "net profit rises": 0.85,
    "revenue up": 0.75, "record revenue": 0.85, "all-time high": 0.85,
    "growth": 0.5, "growth accelerates": 0.75, "outperform": 0.8,
    "expansion": 0.6, "expands": 0.6, "commissioning": 0.7,
    "order win": 0.85, "bags order": 0.85, "contract won": 0.85, "wins contract": 0.85,
    "contract awarded": 0.85, "awarded": 0.7, "bags": 0.65, "secures": 0.7, "wins": 0.6,
    "approved": 0.6, "approval": 0.6, "greenlight": 0.65,
    "dividend": 0.65, "bonus issue": 0.8, "share buyback": 0.8,
    "bullish": 0.7, "upgrade": 0.75, "upgraded": 0.75, "target raised": 0.75,
    "strong demand": 0.7, "beats estimates": 0.85, "in-line": 0.2,
    "debt free": 0.8, "debt reduction": 0.7, "deleveraging": 0.65,
}

NEGATIVE_TERMS = {
    "plunge": -0.85, "plunges": -0.85, "plunged": -0.85,
    "slump": -0.8, "slumps": -0.8, "slumped": -0.8,
    "profit falls": -0.85, "profit drops": -0.85, "loss widens": -0.9,
    "revenue miss": -0.85, "misses estimates": -0.85, "guidance cut": -0.85,
    "decline": -0.5, "declines": -0.5, "declined": -0.5,
    "fine": -0.7, "penalty": -0.75, "penalized": -0.75, "sebi notice": -0.85,
    "investigation": -0.8, "probe": -0.75, "fraud": -0.95, "tax raid": -0.9,
    "downgrade": -0.75, "downgraded": -0.75, "target cut": -0.75,
    "bearish": -0.65, "default": -0.95, "delayed": -0.4,
    "resigns": -0.5, "resignation": -0.5, "cfo quits": -0.75, "ceo steps down": -0.65,
    "dispute": -0.6, "litigation": -0.65, "lawsuit": -0.7,
}

EVENT_PATTERNS = [
    ("EARNINGS", re.compile(r"\b(q[1-4]|earnings|results|net profit|ebitda|revenue|margin|quarterly|audited)\b", re.IGNORECASE)),
    ("CONTRACT_WIN", re.compile(r"\b(order|contract|tender|bags|awarded|supply agreement|deal worth|mou)\b", re.IGNORECASE)),
    ("REGULATORY", re.compile(r"\b(sebi|rbi|cci|enforcement|directorate|tax notice|penalty|probe|audit|compliance|tribunal|nclt)\b", re.IGNORECASE)),
    ("M_AND_A", re.compile(r"\b(acquire|acquisition|merger|demerger|buyout|stake sale|takeover|joint venture)\b", re.IGNORECASE)),
    ("MANAGEMENT", re.compile(r"\b(ceo|cfo|managing director|board of directors|resigns|appointed|resignation|succession)\b", re.IGNORECASE)),
    ("MACRO_POLICY", re.compile(r"\b(budget|inflation|repo rate|monetary policy|rbi policy|tariff|import duty|spectrum)\b", re.IGNORECASE)),
]


class NewsSentimentEngine:
    """
    Financial sentiment analyzer and event classifier for Indian equities.
    Evaluates polarity, confidence, and corporate event categorization.
    """

    def __init__(self, model_version: str = "v1.0.0-rule-finbert"):
        self.model_version = model_version

    def analyze(self, headline: str, summary: Optional[str] = None) -> SentimentAnalysis:
        """
        Analyzes the headline and summary for financial sentiment and event category.
        """
        full_text = f"{headline or ''} {summary or ''}".lower()

        # 1. Calculate sentiment score
        pos_weight = 0.0
        pos_hits = 0
        for term, weight in POSITIVE_TERMS.items():
            if term in full_text:
                pos_weight += weight
                pos_hits += 1

        neg_weight = 0.0
        neg_hits = 0
        for term, weight in NEGATIVE_TERMS.items():
            if term in full_text:
                neg_weight += abs(weight)
                neg_hits += 1

        total_hits = pos_hits + neg_hits
        if total_hits == 0:
            raw_score = 0.0
            label = "NEUTRAL"
            confidence = 0.60
        else:
            net_weight = pos_weight - neg_weight
            # Normalize between -1.0 and +1.0 using hyperbolic tangent
            import math
            raw_score = math.tanh(net_weight / 1.5)
            # Clip between -1.0 and 1.0
            raw_score = round(max(-1.0, min(1.0, raw_score)), 4)

            if raw_score >= 0.15:
                label = "POSITIVE"
                confidence = round(min(0.95, 0.65 + (pos_hits / 5.0) * 0.3), 2)
            elif raw_score <= -0.15:
                label = "NEGATIVE"
                confidence = round(min(0.95, 0.65 + (neg_hits / 5.0) * 0.3), 2)
            else:
                label = "NEUTRAL"
                confidence = 0.70

        # 2. Detect event category
        detected_category = "GENERAL"
        for cat_name, pattern in EVENT_PATTERNS:
            if pattern.search(full_text):
                detected_category = cat_name
                break

        return SentimentAnalysis(
            score=raw_score,
            label=label,
            confidence=confidence,
            event_category=detected_category,
            model_version=self.model_version,
        )
