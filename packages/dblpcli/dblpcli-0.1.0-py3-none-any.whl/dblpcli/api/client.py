"""DBLP API client with retry logic."""

from __future__ import annotations

import os
import random
import time
import xml.etree.ElementTree as ET
from typing import Any, Callable

import httpx


class DBLPError(Exception):
    """Base exception for DBLP API errors."""

    def __init__(self, message: str, code: str | None = None, suggestion: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.suggestion = suggestion


class NotFoundError(DBLPError):
    """Publication or author not found."""

    def __init__(self, message: str, key: str | None = None):
        super().__init__(message, code="NOT_FOUND", suggestion="Try searching with the search command")
        self.key = key


class NetworkError(DBLPError):
    """Network connectivity issues."""

    def __init__(self, message: str):
        super().__init__(message, code="NETWORK_ERROR", suggestion="Check your internet connection")


class DBLPClient:
    """DBLP API client with retry logic and connection pooling."""

    SEARCH_PUBL_URL = "https://dblp.org/search/publ/api"
    SEARCH_AUTHOR_URL = "https://dblp.org/search/author/api"
    SEARCH_VENUE_URL = "https://dblp.org/search/venue/api"
    RECORD_BASE_URL = "https://dblp.org/rec"
    PID_BASE_URL = "https://dblp.org/pid"

    def __init__(
        self,
        max_retries: int | None = None,
        max_retry_wait: int | None = None,
        timeout: float | None = None,
        status_callback: Callable[[str], None] | None = None,
    ):
        self._client: httpx.Client | None = None
        self.max_retries = max_retries if max_retries is not None else int(os.environ.get("DBLP_MAX_RETRIES", "3"))
        self.max_retry_wait = max_retry_wait if max_retry_wait is not None else 60
        self.timeout = timeout if timeout is not None else float(os.environ.get("DBLP_TIMEOUT", "10.0"))
        self.status_callback = status_callback

    @property
    def client(self) -> httpx.Client:
        """Lazy-initialized HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers={
                    "User-Agent": "dblpcli/0.1.0 (https://github.com/mrshu/dblpcli)"
                },
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "DBLPClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Make an HTTP request with retry logic."""
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.request(method, url, **kwargs)

                if response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {url}", key=url)

                if response.status_code == 429:
                    # Rate limited - retry with backoff
                    retry_after = int(response.headers.get("Retry-After", 5))
                    wait_time = min(retry_after, self.max_retry_wait)
                    if attempt < self.max_retries:
                        if self.status_callback:
                            self.status_callback(f"Rate limited, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise DBLPError("Rate limit exceeded", code="RATE_LIMITED")

                if response.status_code >= 500:
                    # Server error - retry with backoff
                    if attempt < self.max_retries:
                        wait_time = min(2 ** attempt + random.uniform(0, 1), self.max_retry_wait)
                        if self.status_callback:
                            self.status_callback(f"Server error, retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    raise DBLPError(f"Server error: {response.status_code}", code="SERVER_ERROR")

                response.raise_for_status()
                return response

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = min(2 ** attempt + random.uniform(0, 1), self.max_retry_wait)
                    if self.status_callback:
                        self.status_callback(f"Timeout, retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue

            except httpx.RequestError as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = min(2 ** attempt + random.uniform(0, 1), self.max_retry_wait)
                    if self.status_callback:
                        self.status_callback(f"Network error, retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue

        raise NetworkError(f"Request failed after {self.max_retries + 1} attempts: {last_error}")

    def _parse_publication_xml(self, xml_str: str) -> dict[str, Any]:
        """Parse a publication XML response into a dict."""
        root = ET.fromstring(xml_str)

        # Find the actual record element (article, inproceedings, etc.)
        record = None
        record_tags = [
            "article", "inproceedings", "proceedings", "book",
            "incollection", "phdthesis", "mastersthesis", "www"
        ]
        for tag in record_tags:
            record = root.find(f".//{tag}")
            if record is not None:
                break

        if record is None:
            # Try to find any element with a key attribute
            for elem in root.iter():
                if elem.get("key"):
                    record = elem
                    break

        if record is None:
            raise DBLPError("Could not parse publication XML", code="PARSE_ERROR")

        result: dict[str, Any] = {
            "key": record.get("key", ""),
            "type": record.tag,
        }

        # Extract title
        title_elem = record.find("title")
        if title_elem is not None:
            result["title"] = "".join(title_elem.itertext()).strip()

        # Extract year
        year_elem = record.find("year")
        if year_elem is not None:
            result["year"] = int(year_elem.text) if year_elem.text else None

        # Extract authors
        authors = []
        for author in record.findall("author"):
            authors.append("".join(author.itertext()).strip())
        if authors:
            result["authors"] = authors

        # Extract venue (booktitle for conf, journal for articles)
        booktitle = record.find("booktitle")
        journal = record.find("journal")
        if booktitle is not None:
            result["venue"] = "".join(booktitle.itertext()).strip()
        elif journal is not None:
            result["venue"] = "".join(journal.itertext()).strip()

        # Extract DOI
        doi_elem = record.find("ee")
        if doi_elem is not None and doi_elem.text:
            ee = doi_elem.text
            if "doi.org/" in ee:
                result["doi"] = ee.split("doi.org/")[-1]
            else:
                result["url"] = ee

        # Extract pages, volume, number
        for field in ["pages", "volume", "number"]:
            elem = record.find(field)
            if elem is not None and elem.text:
                result[field] = elem.text

        return result

    def _parse_search_xml(self, xml_str: str) -> dict[str, Any]:
        """Parse a search API XML response."""
        root = ET.fromstring(xml_str)

        result: dict[str, Any] = {
            "results": [],
            "meta": {}
        }

        # Parse hits info
        hits = root.find(".//hits")
        if hits is not None:
            result["meta"]["total"] = int(hits.get("total", 0))
            result["meta"]["offset"] = int(hits.get("first", 0))
            result["meta"]["limit"] = int(hits.get("sent", 0))

        # Parse completions
        completions = root.find(".//completions")
        if completions is not None:
            comp_list = []
            for c in completions.findall("c"):
                if c.text:
                    comp_list.append(c.text)
            if comp_list:
                result["meta"]["completions"] = comp_list

        # Parse hit entries
        for hit in root.findall(".//hit"):
            info = hit.find("info")
            if info is None:
                continue

            entry: dict[str, Any] = {}

            # Key/URL
            url_elem = info.find("url")
            if url_elem is not None and url_elem.text:
                # Extract key from URL like https://dblp.org/rec/conf/nips/VaswaniSPUJGKP17
                url = url_elem.text
                if "/rec/" in url:
                    entry["key"] = url.split("/rec/")[-1]
                entry["url"] = url

            # Title
            title_elem = info.find("title")
            if title_elem is not None:
                entry["title"] = "".join(title_elem.itertext()).strip()

            # Year
            year_elem = info.find("year")
            if year_elem is not None and year_elem.text:
                entry["year"] = int(year_elem.text)

            # Authors
            authors_elem = info.find("authors")
            if authors_elem is not None:
                authors = []
                for author in authors_elem.findall("author"):
                    if author.text:
                        authors.append(author.text)
                if authors:
                    entry["authors"] = authors

            # Venue
            venue_elem = info.find("venue")
            if venue_elem is not None and venue_elem.text:
                entry["venue"] = venue_elem.text

            # Type
            type_elem = info.find("type")
            if type_elem is not None and type_elem.text:
                entry["type"] = type_elem.text

            # DOI
            doi_elem = info.find("doi")
            if doi_elem is not None and doi_elem.text:
                entry["doi"] = doi_elem.text

            if entry:
                result["results"].append(entry)

        return result

    def _parse_author_search_xml(self, xml_str: str) -> dict[str, Any]:
        """Parse an author search API XML response."""
        root = ET.fromstring(xml_str)

        result: dict[str, Any] = {
            "results": [],
            "meta": {}
        }

        # Parse hits info
        hits = root.find(".//hits")
        if hits is not None:
            result["meta"]["total"] = int(hits.get("total", 0))
            result["meta"]["offset"] = int(hits.get("first", 0))
            result["meta"]["limit"] = int(hits.get("sent", 0))

        # Parse hit entries
        for hit in root.findall(".//hit"):
            info = hit.find("info")
            if info is None:
                continue

            entry: dict[str, Any] = {}

            # URL contains PID
            url_elem = info.find("url")
            if url_elem is not None and url_elem.text:
                url = url_elem.text
                if "/pid/" in url:
                    entry["pid"] = url.split("/pid/")[-1]
                entry["url"] = url

            # Author name
            author_elem = info.find("author")
            if author_elem is not None and author_elem.text:
                entry["name"] = author_elem.text

            # Notes (may contain aliases)
            notes_elem = info.find("notes")
            if notes_elem is not None:
                notes = []
                for note in notes_elem.findall("note"):
                    if note.text:
                        notes.append(note.text)
                if notes:
                    entry["notes"] = notes

            if entry:
                result["results"].append(entry)

        return result

    def _parse_venue_search_xml(self, xml_str: str) -> dict[str, Any]:
        """Parse a venue search API XML response."""
        root = ET.fromstring(xml_str)

        result: dict[str, Any] = {
            "results": [],
            "meta": {}
        }

        # Parse hits info
        hits = root.find(".//hits")
        if hits is not None:
            result["meta"]["total"] = int(hits.get("total", 0))
            result["meta"]["offset"] = int(hits.get("first", 0))
            result["meta"]["limit"] = int(hits.get("sent", 0))

        # Parse hit entries
        for hit in root.findall(".//hit"):
            info = hit.find("info")
            if info is None:
                continue

            entry: dict[str, Any] = {}

            # URL contains venue key
            url_elem = info.find("url")
            if url_elem is not None and url_elem.text:
                url = url_elem.text
                # Extract key from URL like https://dblp.org/db/conf/nips/index.html
                if "/db/" in url:
                    key = url.split("/db/")[-1].replace("/index.html", "").rstrip("/")
                    entry["key"] = key
                entry["url"] = url

            # Venue name
            venue_elem = info.find("venue")
            if venue_elem is not None and venue_elem.text:
                entry["name"] = venue_elem.text

            # Acronym
            acronym_elem = info.find("acronym")
            if acronym_elem is not None and acronym_elem.text:
                entry["acronym"] = acronym_elem.text

            # Type
            type_elem = info.find("type")
            if type_elem is not None and type_elem.text:
                entry["type"] = type_elem.text

            if entry:
                result["results"].append(entry)

        return result

    def _parse_author_xml(self, xml_str: str) -> dict[str, Any]:
        """Parse an author page XML response."""
        root = ET.fromstring(xml_str)

        result: dict[str, Any] = {
            "publications": [],
        }

        # Get author info from dblpperson element
        # The root element might be dblpperson itself
        if root.tag == "dblpperson":
            person = root
        else:
            person = root.find(".//dblpperson")

        if person is not None:
            result["name"] = person.get("name", "")
            result["pid"] = person.get("pid", "")

        # Parse publications
        for tag in ["article", "inproceedings", "proceedings", "book", "incollection", "phdthesis", "mastersthesis"]:
            for record in root.findall(f".//{tag}"):
                pub = self._parse_record_element(record)
                if pub:
                    result["publications"].append(pub)

        return result

    def _parse_record_element(self, record: ET.Element) -> dict[str, Any]:
        """Parse a single publication record element."""
        entry: dict[str, Any] = {
            "key": record.get("key", ""),
            "type": record.tag,
        }

        title_elem = record.find("title")
        if title_elem is not None:
            entry["title"] = "".join(title_elem.itertext()).strip()

        year_elem = record.find("year")
        if year_elem is not None and year_elem.text:
            entry["year"] = int(year_elem.text)

        authors = []
        for author in record.findall("author"):
            authors.append("".join(author.itertext()).strip())
        if authors:
            entry["authors"] = authors

        booktitle = record.find("booktitle")
        journal = record.find("journal")
        if booktitle is not None:
            entry["venue"] = "".join(booktitle.itertext()).strip()
        elif journal is not None:
            entry["venue"] = "".join(journal.itertext()).strip()

        return entry

    # Public API methods

    def search_publications(
        self,
        query: str,
        limit: int = 30,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search publications by query."""
        params = {
            "q": query,
            "format": "xml",
            "h": min(limit, 1000),
            "f": offset,
            "c": 0,  # No completions by default
        }
        response = self._request("GET", self.SEARCH_PUBL_URL, params=params)
        result = self._parse_search_xml(response.text)
        result["meta"]["query"] = query
        return result

    def search_authors(
        self,
        query: str,
        limit: int = 30,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search authors by name."""
        params = {
            "q": query,
            "format": "xml",
            "h": min(limit, 1000),
            "f": offset,
            "c": 0,
        }
        response = self._request("GET", self.SEARCH_AUTHOR_URL, params=params)
        result = self._parse_author_search_xml(response.text)
        result["meta"]["query"] = query
        return result

    def search_venues(
        self,
        query: str,
        limit: int = 30,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search venues by name."""
        params = {
            "q": query,
            "format": "xml",
            "h": min(limit, 1000),
            "f": offset,
            "c": 0,
        }
        response = self._request("GET", self.SEARCH_VENUE_URL, params=params)
        result = self._parse_venue_search_xml(response.text)
        result["meta"]["query"] = query
        return result

    def get_publication(self, key: str) -> dict[str, Any]:
        """Get a publication by its DBLP key."""
        url = f"{self.RECORD_BASE_URL}/{key}.xml"
        response = self._request("GET", url)
        return self._parse_publication_xml(response.text)

    def get_publication_bibtex(self, key: str) -> str:
        """Get BibTeX for a publication directly from DBLP."""
        url = f"{self.RECORD_BASE_URL}/{key}.bib"
        response = self._request("GET", url)
        return response.text

    def get_publications_batch(self, keys: list[str]) -> list[dict[str, Any]]:
        """Get multiple publications by their DBLP keys."""
        results = []
        for key in keys:
            try:
                pub = self.get_publication(key)
                results.append(pub)
            except NotFoundError:
                # Skip not found, but could also collect errors
                pass
        return results

    def get_bibtex_batch(self, keys: list[str]) -> str:
        """Get BibTeX for multiple publications."""
        bibtex_entries = []
        for key in keys:
            try:
                bib = self.get_publication_bibtex(key)
                bibtex_entries.append(bib.strip())
            except NotFoundError:
                pass
        return "\n\n".join(bibtex_entries)

    def get_author(self, pid: str) -> dict[str, Any]:
        """Get an author by their PID."""
        url = f"{self.PID_BASE_URL}/{pid}.xml"
        response = self._request("GET", url)
        return self._parse_author_xml(response.text)

    def get_author_bibtex(self, pid: str) -> str:
        """Get BibTeX for all publications of an author."""
        url = f"{self.PID_BASE_URL}/{pid}.bib"
        response = self._request("GET", url)
        return response.text

    def get_author_publications(
        self,
        pid: str,
        limit: int | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> dict[str, Any]:
        """Get publications for an author with optional filtering."""
        author_data = self.get_author(pid)

        publications = author_data.get("publications", [])

        # Filter by year if specified
        if year_from is not None:
            publications = [p for p in publications if p.get("year", 0) >= year_from]
        if year_to is not None:
            publications = [p for p in publications if p.get("year", 9999) <= year_to]

        # Sort by year descending
        publications.sort(key=lambda p: p.get("year", 0), reverse=True)

        # Apply limit
        if limit is not None:
            publications = publications[:limit]

        return {
            "author": {
                "name": author_data.get("name", ""),
                "pid": author_data.get("pid", pid),
            },
            "publications": publications,
            "meta": {
                "total": len(publications),
            }
        }

    def get_venue_publications(
        self,
        venue_key: str,
        year: int | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get publications from a venue, optionally filtered by year."""
        # Build search query using DBLP's stream syntax
        # e.g., "stream:conf/nips:" or "stream:conf/nips/2023:"
        if year is not None:
            query = f"stream:{venue_key}/{year}:"
        else:
            query = f"stream:{venue_key}:"

        return self.search_publications(query, limit=limit, offset=offset)
