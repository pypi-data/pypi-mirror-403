"""Tests for the CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dblpcli.cli import app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_search_result():
    return {
        "results": [
            {
                "key": "conf/nips/VaswaniSPUJGKP17",
                "title": "Attention is All You Need",
                "year": 2017,
                "authors": ["Ashish Vaswani", "Noam Shazeer"],
                "venue": "NeurIPS",
            }
        ],
        "meta": {
            "query": "transformer",
            "total": 1,
            "offset": 0,
            "limit": 30,
        }
    }


@pytest.fixture
def mock_author_search_result():
    return {
        "results": [
            {
                "pid": "h/GeoffreyEHinton",
                "name": "Geoffrey E. Hinton",
                "notes": ["University of Toronto"],
            }
        ],
        "meta": {
            "query": "Hinton",
            "total": 1,
            "offset": 0,
            "limit": 30,
        }
    }


@pytest.fixture
def mock_venue_search_result():
    return {
        "results": [
            {
                "key": "conf/nips",
                "name": "Neural Information Processing Systems",
                "acronym": "NeurIPS",
                "type": "Conference",
            }
        ],
        "meta": {
            "query": "NeurIPS",
            "total": 1,
            "offset": 0,
            "limit": 30,
        }
    }


@pytest.fixture
def mock_publication():
    return {
        "key": "conf/nips/VaswaniSPUJGKP17",
        "title": "Attention is All You Need",
        "year": 2017,
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "venue": "NeurIPS",
        "type": "inproceedings",
    }


class TestVersion:
    """Test version command."""

    def test_version(self, runner):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "dblpcli" in result.output


class TestSearch:
    """Test search command."""

    def test_search_table_format(self, runner, mock_search_result):
        """Test search with table output."""
        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.search_publications.return_value = mock_search_result
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["search", "transformer"])

        assert result.exit_code == 0
        assert "Attention is All You Need" in result.output
        assert "VaswaniSPUJGKP17" in result.output

    def test_search_json_format(self, runner, mock_search_result):
        """Test search with JSON output."""
        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.search_publications.return_value = mock_search_result
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["search", "transformer", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Attention is All You Need"

    def test_search_with_year(self, runner, mock_search_result):
        """Test search with year filter."""
        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.search_publications.return_value = mock_search_result
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["search", "transformer", "--year", "2017-2020"])

        assert result.exit_code == 0
        # Verify the query was modified
        call_args = mock_client.search_publications.call_args
        assert "year:2017:2020" in call_args[0][0]

    def test_search_with_limit(self, runner, mock_search_result):
        """Test search with limit."""
        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.search_publications.return_value = mock_search_result
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["search", "transformer", "--limit", "10"])

        assert result.exit_code == 0
        call_args = mock_client.search_publications.call_args
        assert call_args[1]["limit"] == 10


class TestPub:
    """Test pub command."""

    def test_pub_table_format(self, runner, mock_publication):
        """Test pub with table output."""
        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_publication.return_value = mock_publication
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["pub", "conf/nips/VaswaniSPUJGKP17"])

        assert result.exit_code == 0
        assert "Attention is All You Need" in result.output

    def test_pub_json_format(self, runner, mock_publication):
        """Test pub with JSON output."""
        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_publication.return_value = mock_publication
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["pub", "conf/nips/VaswaniSPUJGKP17", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["result"]["title"] == "Attention is All You Need"


class TestBibtex:
    """Test bibtex command."""

    def test_bibtex_single(self, runner):
        """Test bibtex for single key."""
        sample_bib = "@inproceedings{DBLP:conf/nips/VaswaniSPUJGKP17,\n  title = {Attention},\n}"

        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_publication_bibtex.return_value = sample_bib
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["bibtex", "conf/nips/VaswaniSPUJGKP17"])

        assert result.exit_code == 0
        assert "@inproceedings" in result.output

    def test_bibtex_custom_key(self, runner):
        """Test bibtex with custom citation key."""
        sample_bib = "@inproceedings{DBLP:conf/nips/VaswaniSPUJGKP17,\n  title = {Attention},\n}"

        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_publication_bibtex.return_value = sample_bib
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["bibtex", "conf/nips/VaswaniSPUJGKP17", "--key", "vaswani2017"])

        assert result.exit_code == 0
        assert "@inproceedings{vaswani2017," in result.output

    def test_bibtex_batch(self, runner):
        """Test bibtex for multiple keys."""
        sample_bib = "@inproceedings{key1,}\n\n@inproceedings{key2,}"

        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_bibtex_batch.return_value = sample_bib
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["bibtex", "key1", "key2"])

        assert result.exit_code == 0
        assert "@inproceedings{key1," in result.output
        assert "@inproceedings{key2," in result.output

    def test_bibtex_custom_key_with_multiple_keys_error(self, runner):
        """Test that --key with multiple keys gives error."""
        result = runner.invoke(app, ["bibtex", "key1", "key2", "--key", "custom"])

        assert result.exit_code == 1
        assert "can only be used with a single" in result.output


class TestAuthorCommands:
    """Test author subcommands."""

    def test_author_search(self, runner, mock_author_search_result):
        """Test author search."""
        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.search_authors.return_value = mock_author_search_result
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["author", "search", "Hinton"])

        assert result.exit_code == 0
        assert "Geoffrey E. Hinton" in result.output

    def test_author_search_json(self, runner, mock_author_search_result):
        """Test author search with JSON output."""
        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.search_authors.return_value = mock_author_search_result
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["author", "search", "Hinton", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["results"][0]["name"] == "Geoffrey E. Hinton"

    def test_author_pubs(self, runner):
        """Test author pubs."""
        mock_result = {
            "author": {"name": "Geoffrey E. Hinton", "pid": "h/GeoffreyEHinton"},
            "publications": [
                {"key": "conf/nips/test", "title": "Test Paper", "year": 2020, "authors": ["Hinton"]}
            ],
            "meta": {"total": 1}
        }

        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_author_publications.return_value = mock_result
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["author", "pubs", "h/GeoffreyEHinton"])

        assert result.exit_code == 0
        assert "Test Paper" in result.output


class TestVenueCommands:
    """Test venue subcommands."""

    def test_venue_search(self, runner, mock_venue_search_result):
        """Test venue search."""
        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.search_venues.return_value = mock_venue_search_result
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["venue", "search", "NeurIPS"])

        assert result.exit_code == 0
        assert "Neural Information Processing Systems" in result.output

    def test_venue_search_json(self, runner, mock_venue_search_result):
        """Test venue search with JSON output."""
        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.search_venues.return_value = mock_venue_search_result
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["venue", "search", "NeurIPS", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["results"][0]["acronym"] == "NeurIPS"

    def test_venue_pubs(self, runner, mock_search_result):
        """Test venue pubs."""
        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_venue_publications.return_value = mock_search_result
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["venue", "pubs", "conf/nips", "--year", "2023"])

        assert result.exit_code == 0
        mock_client.get_venue_publications.assert_called_with("conf/nips", year=2023, limit=30, offset=0)


class TestErrorHandling:
    """Test error handling."""

    def test_not_found_error_table(self, runner):
        """Test not found error with table format."""
        from dblpcli.api import NotFoundError

        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_publication.side_effect = NotFoundError("Not found", key="invalid/key")
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["pub", "invalid/key"])

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_not_found_error_json(self, runner):
        """Test not found error with JSON format."""
        from dblpcli.api import NotFoundError

        with patch("dblpcli.cli.DBLPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.get_publication.side_effect = NotFoundError("Not found", key="invalid/key")
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, ["pub", "invalid/key", "--format", "json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
