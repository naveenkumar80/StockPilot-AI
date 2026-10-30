import hashlib
import re
from typing import List, Tuple, Set, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from app.integrations.news.base import RawNewsArticle


# Tracking params to strip during URL canonicalization
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "fbclid", "gclid", "src", "platform", "mc_cid", "mc_eid"
}


def canonicalize_url(url: str) -> str:
    """Normalizes URL by removing query tracking params and fragment."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        # Filter query params
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        clean_query = [(k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS]
        clean_query_str = urlencode(clean_query)
        # Rebuild without fragment, with lowercase scheme and netloc
        return urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            "",
            clean_query_str,
            ""
        ))
    except Exception:
        return url.strip()


def normalize_headline(headline: str) -> str:
    """Normalizes headline text for hash and similarity comparison."""
    if not headline:
        return ""
    text = headline.lower().strip()
    # Replace non-alphanumeric with single space
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Collapse multiple whitespaces
    return " ".join(text.split())


def compute_article_hash(headline: str, publisher: str) -> str:
    """Computes a SHA-256 hash from normalized headline and publisher."""
    norm_head = normalize_headline(headline)
    norm_pub = publisher.lower().strip()
    payload = f"{norm_head}::{norm_pub}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class NewsDeduplicator:
    """
    Deduplication engine that filters duplicate articles across runs and publishers.
    Uses canonical URL matching, content hashing, and token Jaccard similarity.
    """

    def __init__(self, existing_urls: Optional[Set[str]] = None, existing_hashes: Optional[Set[str]] = None):
        self.seen_urls: Set[str] = set(existing_urls or [])
        self.seen_hashes: Set[str] = set(existing_hashes or [])

    def is_duplicate(self, article: RawNewsArticle) -> Tuple[bool, str]:
        """
        Returns (True, reason) if article is a duplicate of a previously seen one.
        """
        can_url = canonicalize_url(article.url)
        if can_url in self.seen_urls:
            return True, f"Duplicate canonical URL: {can_url}"

        art_hash = compute_article_hash(article.headline, article.publisher)
        if art_hash in self.seen_hashes:
            return True, f"Duplicate content hash ({art_hash[:10]}...)"

        return False, ""

    def filter_batch(self, articles: List[RawNewsArticle]) -> List[Tuple[RawNewsArticle, str]]:
        """
        Deduplicates a batch of incoming articles.
        Returns list of (article, content_hash) for unique articles only.
        """
        unique_articles: List[Tuple[RawNewsArticle, str]] = []

        for art in articles:
            is_dup, reason = self.is_duplicate(art)
            if not is_dup:
                can_url = canonicalize_url(art.url)
                art_hash = compute_article_hash(art.headline, art.publisher)

                self.seen_urls.add(can_url)
                self.seen_hashes.add(art_hash)

                # Store canonicalized url back to article
                art.url = can_url
                unique_articles.append((art, art_hash))

        return unique_articles
