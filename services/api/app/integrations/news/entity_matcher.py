import re
from typing import Dict, List, Set, Optional, Tuple
from app.integrations.news.base import EntityMatch


# Canonical aliases dictionary for top Indian equities
COMPANY_ALIASES: Dict[str, List[str]] = {
    "RELIANCE": ["reliance industries", "ril", "reliance retail", "reliance jio", "jio platforms", "mukesh ambani"],
    "TCS": ["tata consultancy services", "tcs"],
    "INFY": ["infosys", "infosys tech", "salil parekh"],
    "HDFCBANK": ["hdfc bank", "hdfc", "housing development finance"],
    "ICICIBANK": ["icici bank", "icici"],
    "SBIN": ["state bank of india", "sbi"],
    "BHARTIARTL": ["bharti airtel", "airtel", "sunil mittal"],
    "TATAMOTORS": ["tata motors", "tamo", "jaguar land rover", "jlr"],
    "ADANIPORTS": ["adani ports", "apsez", "adani port", "gautam adani"],
    "BEL": ["bharat electronics", "bel"],
    "NTPC": ["ntpc", "national thermal power"],
    "POWERGRID": ["power grid", "powergrid", "pgcil"],
    "LT": ["larsen & toubro", "l&t", "larsen and toubro"],
    "ITC": ["itc ltd", "itc limited"],
    "TITAN": ["titan company", "titan"],
}


class NewsEntityMatcher:
    """
    Identifies which stock instruments are mentioned in a news headline and body.
    Computes a relevance score based on field location and match specificity.
    """

    def __init__(self, tracked_symbols: Optional[List[str]] = None, symbol_to_id: Optional[Dict[str, str]] = None):
        self.tracked_symbols: List[str] = tracked_symbols or list(COMPANY_ALIASES.keys())
        self.symbol_to_id: Dict[str, str] = symbol_to_id or {}

        # Compile word-boundary regexes for each symbol
        self._symbol_patterns: Dict[str, re.Pattern] = {
            sym: re.compile(rf"\b{re.escape(sym)}\b", re.IGNORECASE)
            for sym in self.tracked_symbols
        }

    def match_article(self, headline: str, summary: Optional[str] = None) -> List[EntityMatch]:
        """
        Scans headline and optional summary to detect associated instruments.
        Returns a deduplicated list of EntityMatch objects sorted by relevance descending.
        """
        matches: Dict[str, EntityMatch] = {}
        head_text = headline or ""
        sum_text = summary or ""

        for sym in self.tracked_symbols:
            inst_id = self.symbol_to_id.get(sym)

            # 1. Exact symbol in headline (Highest confidence: 1.0)
            if self._symbol_patterns[sym].search(head_text):
                matches[sym] = EntityMatch(
                    symbol=sym,
                    instrument_id=inst_id,
                    relevance_score=1.0,
                    matched_term=sym,
                )
                continue

            # 2. Company alias in headline (High confidence: 0.85)
            aliases = COMPANY_ALIASES.get(sym, [])
            matched_alias = None
            for alias in aliases:
                pattern = rf"\b{re.escape(alias)}\b"
                if re.search(pattern, head_text, re.IGNORECASE):
                    matched_alias = alias
                    break

            if matched_alias:
                matches[sym] = EntityMatch(
                    symbol=sym,
                    instrument_id=inst_id,
                    relevance_score=0.85,
                    matched_term=matched_alias,
                )
                continue

            # 3. Exact symbol in summary/body (Medium confidence: 0.60)
            if sum_text and self._symbol_patterns[sym].search(sum_text):
                matches[sym] = EntityMatch(
                    symbol=sym,
                    instrument_id=inst_id,
                    relevance_score=0.60,
                    matched_term=sym,
                )
                continue

            # 4. Company alias in summary/body (Moderate confidence: 0.45)
            if sum_text:
                for alias in aliases:
                    pattern = rf"\b{re.escape(alias)}\b"
                    if re.search(pattern, sum_text, re.IGNORECASE):
                        matches[sym] = EntityMatch(
                            symbol=sym,
                            instrument_id=inst_id,
                            relevance_score=0.45,
                            matched_term=alias,
                        )
                        break

        # Sort by relevance score descending
        return sorted(matches.values(), key=lambda m: m.relevance_score, reverse=True)
