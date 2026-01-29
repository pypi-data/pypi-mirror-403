"""Tests for the DBLP API client."""

import pytest
from pytest_httpx import HTTPXMock

from dblpcli.api import DBLPClient, NotFoundError


class TestDBLPClientParsing:
    """Test XML parsing methods."""

    def test_parse_publication_search(self, sample_publication_search_xml):
        """Test parsing publication search results."""
        client = DBLPClient()
        result = client._parse_search_xml(sample_publication_search_xml)

        assert "results" in result
        assert "meta" in result
        assert result["meta"]["total"] == 1523
        assert len(result["results"]) == 2

        # Check first result
        pub = result["results"][0]
        assert pub["key"] == "conf/nips/VaswaniSPUJGKP17"
        assert pub["title"] == "Attention is All You Need"
        assert pub["year"] == 2017
        assert "Ashish Vaswani" in pub["authors"]
        assert pub["venue"] == "NeurIPS"

    def test_parse_author_search(self, sample_author_search_xml):
        """Test parsing author search results."""
        client = DBLPClient()
        result = client._parse_author_search_xml(sample_author_search_xml)

        assert "results" in result
        assert result["meta"]["total"] == 5
        assert len(result["results"]) == 2

        # Check first result
        author = result["results"][0]
        assert author["pid"] == "h/GeoffreyEHinton"
        assert author["name"] == "Geoffrey E. Hinton"
        assert "University of Toronto" in author["notes"]

    def test_parse_venue_search(self, sample_venue_search_xml):
        """Test parsing venue search results."""
        client = DBLPClient()
        result = client._parse_venue_search_xml(sample_venue_search_xml)

        assert "results" in result
        assert result["meta"]["total"] == 3
        assert len(result["results"]) == 2

        # Check first result
        venue = result["results"][0]
        assert venue["key"] == "conf/nips"
        assert venue["name"] == "Neural Information Processing Systems"
        assert venue["acronym"] == "NeurIPS"
        assert venue["type"] == "Conference"

    def test_parse_publication_xml(self, sample_publication_xml):
        """Test parsing single publication XML."""
        client = DBLPClient()
        result = client._parse_publication_xml(sample_publication_xml)

        assert result["key"] == "conf/nips/VaswaniSPUJGKP17"
        assert result["title"] == "Attention is All You Need"
        assert result["year"] == 2017
        assert len(result["authors"]) == 8
        assert result["venue"] == "NeurIPS"
        assert result["type"] == "inproceedings"

    def test_parse_author_xml(self, sample_author_xml):
        """Test parsing author page XML."""
        client = DBLPClient()
        result = client._parse_author_xml(sample_author_xml)

        assert result["name"] == "Geoffrey E. Hinton"
        assert result["pid"] == "h/GeoffreyEHinton"
        assert len(result["publications"]) == 2

        # Check publications are parsed
        pubs = result["publications"]
        keys = [p["key"] for p in pubs]
        assert "journals/nature/HintonS06" in keys
        assert "conf/nips/KrizhevskySH12" in keys


class TestDBLPClientRequests:
    """Test HTTP request handling."""

    def test_search_publications(self, httpx_mock: HTTPXMock, sample_publication_search_xml):
        """Test publication search request."""
        httpx_mock.add_response(
            url="https://dblp.org/search/publ/api?q=transformer&format=xml&h=30&f=0&c=0",
            text=sample_publication_search_xml,
        )

        with DBLPClient() as client:
            result = client.search_publications("transformer")

        assert result["meta"]["query"] == "transformer"
        assert len(result["results"]) == 2

    def test_search_authors(self, httpx_mock: HTTPXMock, sample_author_search_xml):
        """Test author search request."""
        httpx_mock.add_response(
            url="https://dblp.org/search/author/api?q=Hinton&format=xml&h=30&f=0&c=0",
            text=sample_author_search_xml,
        )

        with DBLPClient() as client:
            result = client.search_authors("Hinton")

        assert result["meta"]["query"] == "Hinton"
        assert len(result["results"]) == 2

    def test_search_venues(self, httpx_mock: HTTPXMock, sample_venue_search_xml):
        """Test venue search request."""
        httpx_mock.add_response(
            url="https://dblp.org/search/venue/api?q=NeurIPS&format=xml&h=30&f=0&c=0",
            text=sample_venue_search_xml,
        )

        with DBLPClient() as client:
            result = client.search_venues("NeurIPS")

        assert result["meta"]["query"] == "NeurIPS"
        assert len(result["results"]) == 2

    def test_get_publication(self, httpx_mock: HTTPXMock, sample_publication_xml):
        """Test getting a single publication."""
        httpx_mock.add_response(
            url="https://dblp.org/rec/conf/nips/VaswaniSPUJGKP17.xml",
            text=sample_publication_xml,
        )

        with DBLPClient() as client:
            result = client.get_publication("conf/nips/VaswaniSPUJGKP17")

        assert result["key"] == "conf/nips/VaswaniSPUJGKP17"
        assert result["title"] == "Attention is All You Need"

    def test_get_publication_bibtex(self, httpx_mock: HTTPXMock, sample_bibtex):
        """Test getting BibTeX for a publication."""
        httpx_mock.add_response(
            url="https://dblp.org/rec/conf/nips/VaswaniSPUJGKP17.bib",
            text=sample_bibtex,
        )

        with DBLPClient() as client:
            result = client.get_publication_bibtex("conf/nips/VaswaniSPUJGKP17")

        assert "@inproceedings" in result
        assert "Attention is All You Need" in result

    def test_get_author(self, httpx_mock: HTTPXMock, sample_author_xml):
        """Test getting an author by PID."""
        httpx_mock.add_response(
            url="https://dblp.org/pid/h/GeoffreyEHinton.xml",
            text=sample_author_xml,
        )

        with DBLPClient() as client:
            result = client.get_author("h/GeoffreyEHinton")

        assert result["name"] == "Geoffrey E. Hinton"
        assert len(result["publications"]) == 2

    def test_not_found_error(self, httpx_mock: HTTPXMock):
        """Test 404 handling."""
        httpx_mock.add_response(
            url="https://dblp.org/rec/invalid/key.xml",
            status_code=404,
        )

        with DBLPClient() as client:
            with pytest.raises(NotFoundError):
                client.get_publication("invalid/key")

    def test_batch_bibtex(self, httpx_mock: HTTPXMock, sample_bibtex):
        """Test batch BibTeX retrieval."""
        httpx_mock.add_response(
            url="https://dblp.org/rec/conf/nips/VaswaniSPUJGKP17.bib",
            text=sample_bibtex,
        )
        httpx_mock.add_response(
            url="https://dblp.org/rec/conf/nips/KrizhevskySH12.bib",
            text="@inproceedings{DBLP:conf/nips/KrizhevskySH12,\n  title = {ImageNet},\n}",
        )

        with DBLPClient() as client:
            result = client.get_bibtex_batch([
                "conf/nips/VaswaniSPUJGKP17",
                "conf/nips/KrizhevskySH12"
            ])

        assert "@inproceedings{DBLP:conf/nips/VaswaniSPUJGKP17" in result
        assert "@inproceedings{DBLP:conf/nips/KrizhevskySH12" in result


class TestDBLPClientRetry:
    """Test retry behavior."""

    def test_retry_on_server_error(self, httpx_mock: HTTPXMock, sample_publication_search_xml):
        """Test retry on 500 error."""
        # First request fails, second succeeds
        httpx_mock.add_response(status_code=500)
        httpx_mock.add_response(text=sample_publication_search_xml)

        with DBLPClient(max_retries=2, max_retry_wait=0) as client:
            result = client.search_publications("test")

        assert len(result["results"]) == 2

    def test_max_retries_exceeded(self, httpx_mock: HTTPXMock):
        """Test that max retries is respected."""
        from dblpcli.api import DBLPError

        # max_retries=2 means 3 total attempts (initial + 2 retries)
        for _ in range(3):
            httpx_mock.add_response(status_code=500)

        with DBLPClient(max_retries=2, max_retry_wait=0) as client:
            with pytest.raises(DBLPError) as exc_info:
                client.search_publications("test")
            assert exc_info.value.code == "SERVER_ERROR"
