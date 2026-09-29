"""
Pluggable tender source adapters.

Hard constraint: NO scraping of appeloffres.net/appeloffres.com.
Only allowed sources:
1. SimulatedFeedSource — reads from local JSON/CSV files.
2. StaticPageSource — skeleton for official ministry/TUNEPS pages
   that checks robots.txt before fetching.
"""

import csv
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


# Sites we must NEVER scrape
BLOCKED_DOMAINS = frozenset([
    "appeloffres.net",
    "appeloffres.com",
    "www.appeloffres.net",
    "www.appeloffres.com",
])


class TenderSource(ABC):
    """Abstract adapter for fetching tender items."""

    @abstractmethod
    def fetch(self) -> List[Dict]:
        """
        Fetch tender items from the source.

        Returns:
            List of dicts with at least 'id' and 'description' fields.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Source name for logging/tracking."""
        ...


class SimulatedFeedSource(TenderSource):
    """
    Reads tenders from a local JSON or CSV file.

    Used for demos and testing. Never hits the network.
    """

    def __init__(self, filepath: str):
        self._path = Path(filepath)
        if not self._path.exists():
            raise FileNotFoundError(f"Simulated feed file not found: {filepath}")

    def fetch(self) -> List[Dict]:
        suffix = self._path.suffix.lower()

        if suffix == ".json":
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "items" in data:
                    return data["items"]
                else:
                    return [data]

        elif suffix == ".csv":
            with open(self._path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return [dict(row) for row in reader]

        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. Use .json or .csv."
            )

    @property
    def name(self) -> str:
        return f"simulated:{self._path.name}"


class StaticPageSource(TenderSource):
    """
    Skeleton adapter for official ministry / TUNEPS public listing pages.

    Checks robots.txt before fetching. Skips disallowed URLs.
    Does NOT scrape appeloffres.net/.com (blocked by hard constraint).

    NOTE: This is a skeleton — the actual parsing logic for specific
    government sites must be implemented per-site by the team.
    """

    def __init__(self, base_url: str, parse_fn=None):
        """
        Args:
            base_url: The base URL of the tender listing page.
            parse_fn: Optional callable(html: str) -> List[Dict].
                      If not provided, returns empty list.
        """
        parsed = urlparse(base_url)
        domain = parsed.hostname or ""

        if domain.lower() in BLOCKED_DOMAINS:
            raise ValueError(
                f"Domain '{domain}' is blocked. "
                f"appeloffres.net/.com disallow automated access via robots.txt."
            )

        self._base_url = base_url
        self._domain = domain
        self._parse_fn = parse_fn

    def _check_robots_txt(self, url: str) -> bool:
        """
        Check if the URL is allowed by robots.txt.

        Returns True if allowed, False if disallowed.
        """
        try:
            from urllib.robotparser import RobotFileParser

            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()

            allowed = rp.can_fetch("*", url)
            if not allowed:
                logger.warning("URL disallowed by robots.txt: %s", url)
            return allowed
        except Exception as e:
            logger.warning(
                "Cannot read robots.txt for %s: %s. Skipping URL.",
                url, e,
            )
            return False

    def fetch(self) -> List[Dict]:
        """Fetch and parse tenders from the page."""
        if not self._check_robots_txt(self._base_url):
            logger.warning(
                "Skipping %s — disallowed by robots.txt", self._base_url
            )
            return []

        if self._parse_fn is None:
            logger.info(
                "StaticPageSource for %s has no parse function. "
                "Implement a parser for this site.",
                self._base_url,
            )
            return []

        try:
            import httpx

            response = httpx.get(self._base_url, timeout=30, follow_redirects=True)
            response.raise_for_status()
            return self._parse_fn(response.text)
        except Exception as e:
            logger.error("Failed to fetch %s: %s", self._base_url, e)
            return []

    @property
    def name(self) -> str:
        return f"static:{self._domain}"
