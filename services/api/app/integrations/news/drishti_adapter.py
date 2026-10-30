from datetime import datetime, timedelta
from typing import List, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.integrations.news.base import NewsSourceAdapter, RawNewsArticle


# Curated realistic mock exchange disclosures for demo / unauthenticated development mode
SAMPLE_EXCHANGE_FILINGS = [
    {
        "symbol": "RELIANCE",
        "headline": "Reliance Industries announces commissioning of 10GW solar giga-factory at Jamnagar",
        "summary": "RIL intimates stock exchanges regarding the successful mechanical completion and commissioning of its first phase new energy giga-complex.",
        "publisher": "NSE Corporate Announcements",
        "source_type": "EXCHANGE_FILING",
        "url_suffix": "ril-solar-commissioning-2026",
        "hours_ago": 2,
    },
    {
        "symbol": "TCS",
        "headline": "TCS signs $1.2 billion digital transformation mega-deal with European retail giant",
        "summary": "Tata Consultancy Services informs exchanges of a multi-year cloud and AI modernization contract extension.",
        "publisher": "BSE Corporate Announcements",
        "source_type": "EXCHANGE_FILING",
        "url_suffix": "tcs-europe-retail-deal-2026",
        "hours_ago": 4,
    },
    {
        "symbol": "INFY",
        "headline": "Infosys clarifies media reports on executive committee restructuring",
        "summary": "Company clarifies that leadership adjustments are part of planned succession and organizational realignment.",
        "publisher": "NSE Corporate Announcements",
        "source_type": "EXCHANGE_FILING",
        "url_suffix": "infosys-leadership-clarification-2026",
        "hours_ago": 6,
    },
    {
        "symbol": "HDFCBANK",
        "headline": "HDFC Bank board approves dividend distribution and Q3 financial results timeline",
        "summary": "The Board of Directors is scheduled to meet on November 14 to consider financial statements and interim dividend.",
        "publisher": "BSE Corporate Announcements",
        "source_type": "EXCHANGE_FILING",
        "url_suffix": "hdfc-bank-board-meeting-intimation",
        "hours_ago": 9,
    },
    {
        "symbol": "BEL",
        "headline": "Bharat Electronics receives orders worth Rs 2,670 crore from Indian Defence forces",
        "summary": "Orders include radar systems, secure communication devices, and electronic warfare payload suites.",
        "publisher": "NSE Corporate Announcements",
        "source_type": "EXCHANGE_FILING",
        "url_suffix": "bel-order-win-defence-2026",
        "hours_ago": 12,
    },
    {
        "symbol": "SBIN",
        "headline": "State Bank of India raises Rs 10,000 crore via infrastructure bond issuance at 7.28%",
        "summary": "The issue received overwhelming response with bids exceeding 3.5 times the base issue size.",
        "publisher": "BSE Corporate Announcements",
        "source_type": "EXCHANGE_FILING",
        "url_suffix": "sbi-infra-bond-issuance-2026",
        "hours_ago": 18,
    },
    {
        "symbol": "ADANIPORTS",
        "headline": "Adani Ports handles record cargo volume of 42 MMT in October, up 14% year-on-year",
        "summary": "Growth driven by container traffic expansion across Mundra, Vizhinjam, and Dhamra deepwater ports.",
        "publisher": "NSE Corporate Announcements",
        "source_type": "EXCHANGE_FILING",
        "url_suffix": "adani-ports-cargo-milestone-2026",
        "hours_ago": 24,
    },
]


class DrishtiAdapter(NewsSourceAdapter):
    """
    Adapter for Drishti API and official stock exchange corporate announcements (NSE/BSE).
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.DRISHTI_API_KEY
        self.base_url = (base_url or "https://api.drishti.in/v1").rstrip("/")

    @property
    def name(self) -> str:
        return "drishti_exchange_disclosures"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def fetch_latest(self, limit: int = 50) -> List[RawNewsArticle]:
        if not self.is_configured:
            return self._generate_synthetic_filings(limit)

        url = f"{self.base_url}/announcements/latest"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers, params={"limit": limit})
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", data) if isinstance(data, dict) else data
                articles = []
                for item in items:
                    articles.append(RawNewsArticle(
                        headline=item.get("headline", ""),
                        url=item.get("url", ""),
                        publisher=item.get("publisher", "NSE/BSE Filings"),
                        published_at=datetime.fromisoformat(item["published_at"].replace("Z", "+00:00")),
                        summary=item.get("summary"),
                        source_type="EXCHANGE_FILING",
                        external_id=str(item.get("id")),
                    ))
                return articles
        except Exception as e:
            logger.warning(f"[DrishtiAdapter] Live fetch failed: {e}. Falling back to demo filings.")

        return self._generate_synthetic_filings(limit)

    async def fetch_for_symbol(self, symbol: str, limit: int = 20) -> List[RawNewsArticle]:
        all_filings = await self.fetch_latest(limit=100)
        sym_clean = symbol.upper()
        return [f for f in all_filings if sym_clean in f.headline.upper() or sym_clean in (f.summary or "").upper()][:limit]

    def _generate_synthetic_filings(self, limit: int) -> List[RawNewsArticle]:
        now = datetime.utcnow()
        articles = []
        for item in SAMPLE_EXCHANGE_FILINGS[:limit]:
            pub_time = now - timedelta(hours=item["hours_ago"])
            articles.append(RawNewsArticle(
                headline=item["headline"],
                url=f"https://www.bseindia.com/corporates/announcements/{item['url_suffix']}",
                publisher=item["publisher"],
                published_at=pub_time,
                summary=item["summary"],
                source_type=item["source_type"],
                external_id=item["url_suffix"],
                metadata={"symbol_hint": item["symbol"]},
            ))
        return articles
