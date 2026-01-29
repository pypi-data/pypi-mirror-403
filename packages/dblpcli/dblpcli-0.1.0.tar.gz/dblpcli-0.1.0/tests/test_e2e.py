"""End-to-end tests that hit the real DBLP API.

These tests are marked with @pytest.mark.e2e and can be skipped with:
    pytest -m "not e2e"

Or run only e2e tests with:
    pytest -m e2e
"""

import json

import pytest
from typer.testing import CliRunner

from dblpcli.api import DBLPClient
from dblpcli.cli import app

pytestmark = pytest.mark.e2e


@pytest.fixture
def runner():
    return CliRunner()


class TestE2ESearch:
    """End-to-end tests for search functionality."""

    def test_search_publications(self, runner):
        """Test searching for publications."""
        result = runner.invoke(app, ["search", "attention is all you need", "--limit", "5"])

        assert result.exit_code == 0
        assert "Attention" in result.output or "attention" in result.output.lower()

    def test_search_publications_json(self, runner):
        """Test search with JSON output."""
        result = runner.invoke(app, ["search", "transformer", "--limit", "3", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data
        assert "meta" in data
        assert len(data["results"]) <= 3

    def test_search_with_year_filter(self, runner):
        """Test search with year filter."""
        result = runner.invoke(
            app, ["search", "deep learning", "--year", "2020-2022", "--limit", "5", "--format", "json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data
        # All results should be within year range (if any returned)
        for pub in data["results"]:
            if "year" in pub:
                assert 2020 <= pub["year"] <= 2022


class TestE2EPub:
    """End-to-end tests for pub command."""

    def test_get_publication(self, runner):
        """Test getting a known publication."""
        # The famous "Attention is All You Need" paper
        result = runner.invoke(app, ["pub", "conf/nips/VaswaniSPUJGKP17"])

        assert result.exit_code == 0
        assert "Attention" in result.output

    def test_get_publication_json(self, runner):
        """Test getting a publication in JSON format."""
        result = runner.invoke(app, ["pub", "conf/nips/VaswaniSPUJGKP17", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "result" in data
        assert data["result"]["key"] == "conf/nips/VaswaniSPUJGKP17"
        assert "Attention" in data["result"]["title"]

    def test_get_nonexistent_publication(self, runner):
        """Test getting a non-existent publication."""
        result = runner.invoke(app, ["pub", "conf/fake/NotReal12345"])

        assert result.exit_code == 1
        assert "Error" in result.output or "not found" in result.output.lower()


class TestE2EBibtex:
    """End-to-end tests for bibtex command."""

    def test_bibtex_single(self, runner):
        """Test getting BibTeX for a publication."""
        result = runner.invoke(app, ["bibtex", "conf/nips/VaswaniSPUJGKP17"])

        assert result.exit_code == 0
        assert "@" in result.output  # BibTeX entry marker
        assert "Vaswani" in result.output
        assert "2017" in result.output

    def test_bibtex_custom_key(self, runner):
        """Test BibTeX with custom citation key."""
        result = runner.invoke(app, ["bibtex", "conf/nips/VaswaniSPUJGKP17", "--key", "vaswani2017attention"])

        assert result.exit_code == 0
        assert "vaswani2017attention" in result.output

    def test_bibtex_batch(self, runner):
        """Test batch BibTeX retrieval."""
        result = runner.invoke(app, ["bibtex", "conf/nips/VaswaniSPUJGKP17", "conf/nips/KrizhevskySH12"])

        assert result.exit_code == 0
        # Should contain entries for both papers
        assert "Vaswani" in result.output or "vaswani" in result.output.lower()
        assert "Krizhevsky" in result.output or "krizhevsky" in result.output.lower()


class TestE2EAuthor:
    """End-to-end tests for author commands."""

    def test_author_search(self, runner):
        """Test searching for authors."""
        result = runner.invoke(app, ["author", "search", "Geoffrey Hinton", "--limit", "5"])

        assert result.exit_code == 0
        assert "Hinton" in result.output

    def test_author_search_json(self, runner):
        """Test author search with JSON output."""
        result = runner.invoke(app, ["author", "search", "Yann LeCun", "--limit", "3", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data
        # Should find at least one result
        assert len(data["results"]) >= 1

    def test_author_pubs(self, runner):
        """Test getting author publications."""
        # Use a known author PID (Yoshua Bengio = 56/953)
        result = runner.invoke(app, ["author", "pubs", "56/953", "--limit", "5"])

        assert result.exit_code == 0
        # Should show some publications

    def test_author_pubs_json(self, runner):
        """Test author publications with JSON output."""
        result = runner.invoke(app, ["author", "pubs", "56/953", "--limit", "5", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "publications" in data
        assert "author" in data

    def test_author_bibtex(self, runner):
        """Test getting author BibTeX (limited subset)."""
        # This may return a lot of data, so we just check it works
        # Use Yoshua Bengio = 56/953
        result = runner.invoke(app, ["author", "bibtex", "56/953"])

        # May take a while but should succeed
        assert result.exit_code == 0
        assert "@" in result.output  # Should have BibTeX entries


class TestE2EVenue:
    """End-to-end tests for venue commands."""

    def test_venue_search(self, runner):
        """Test searching for venues."""
        result = runner.invoke(app, ["venue", "search", "NeurIPS", "--limit", "5"])

        assert result.exit_code == 0
        assert "NeurIPS" in result.output or "Neural" in result.output

    def test_venue_search_json(self, runner):
        """Test venue search with JSON output."""
        result = runner.invoke(app, ["venue", "search", "ICML", "--limit", "3", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data

    def test_venue_pubs(self, runner):
        """Test getting venue publications."""
        result = runner.invoke(app, ["venue", "pubs", "conf/nips", "--year", "2023", "--limit", "5"])

        assert result.exit_code == 0

    def test_venue_pubs_json(self, runner):
        """Test venue publications with JSON output."""
        result = runner.invoke(
            app, ["venue", "pubs", "conf/icml", "--year", "2023", "--limit", "5", "--format", "json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data


class TestE2EAPIClient:
    """End-to-end tests for the API client directly."""

    def test_search_publications(self):
        """Test publication search via API client."""
        with DBLPClient() as client:
            result = client.search_publications("machine learning", limit=5)

        assert "results" in result
        assert "meta" in result
        assert len(result["results"]) <= 5

    def test_get_publication(self):
        """Test getting a publication via API client."""
        with DBLPClient() as client:
            result = client.get_publication("conf/nips/VaswaniSPUJGKP17")

        assert result["key"] == "conf/nips/VaswaniSPUJGKP17"
        assert "Attention" in result["title"]
        assert result["year"] == 2017

    def test_get_bibtex(self):
        """Test getting BibTeX via API client."""
        with DBLPClient() as client:
            result = client.get_publication_bibtex("conf/nips/VaswaniSPUJGKP17")

        assert "@" in result
        assert "2017" in result

    def test_search_authors(self):
        """Test author search via API client."""
        with DBLPClient() as client:
            result = client.search_authors("Hinton", limit=5)

        assert "results" in result
        assert len(result["results"]) >= 1
        # Should find Geoffrey Hinton
        names = [a.get("name", "") for a in result["results"]]
        assert any("Hinton" in name for name in names)

    def test_search_venues(self):
        """Test venue search via API client."""
        with DBLPClient() as client:
            result = client.search_venues("NeurIPS", limit=5)

        assert "results" in result
        assert len(result["results"]) >= 1
