"""Main CLI application for dblpcli."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer

from dblpcli import __version__
from dblpcli.api import DBLPClient, DBLPError, NotFoundError
from dblpcli.formatters import format_json, format_table
from dblpcli.formatters.json_formatter import format_error_json

app = typer.Typer(
    name="dblpcli",
    help="""CLI for DBLP, for humans and agents alike.

Search and retrieve publications, authors, and venues from the DBLP
computer science bibliography. Export BibTeX directly from DBLP.

Typical workflow:
  1. Search: dblpcli search "query" --format json
  2. Get details: dblpcli pub <key> --format json
  3. Export BibTeX: dblpcli bibtex <key> [<key2> ...]

Output formats (--format / -f):
  table   Human-readable table (default)
  json    Structured JSON for programmatic use

JSON output structure:
  Search results: {"results": [...], "meta": {"total": N, "query": "..."}}
  Single item: {"result": {...}, "meta": {...}}
  Errors: {"error": {"code": "...", "message": "..."}}

Key identifiers:
  Publication key: conf/nips/VaswaniSPUJGKP17, journals/jmlr/Author23
  Author PID: 56/953, h/GeoffreyEHinton (find via 'author search')
  Venue key: conf/nips, journals/jmlr
""",
    no_args_is_help=True,
)

author_app = typer.Typer(
    help="""Search authors and retrieve their publications.

Workflow:
  1. Find author: dblpcli author search "Name" --format json
  2. Get PID from results (e.g., "56/953" or "h/GeoffreyEHinton")
  3. Get publications: dblpcli author pubs <pid> --format json
  4. Export BibTeX: dblpcli author bibtex <pid>

The PID (persistent identifier) is stable and won't change.
"""
)
venue_app = typer.Typer(
    help="""Search venues and retrieve their publications.

Venue types:
  conf/     Conferences (e.g., conf/nips, conf/icml)
  journals/ Journals (e.g., journals/jmlr, journals/tnn)

Workflow:
  1. Find venue: dblpcli venue search "NeurIPS" --format json
  2. Get publications: dblpcli venue pubs conf/nips --year 2023 --format json
"""
)

app.add_typer(author_app, name="author")
app.add_typer(venue_app, name="venue")


class OutputFormat(str, Enum):
    """Output format options."""

    TABLE = "table"
    JSON = "json"
    BIBTEX = "bibtex"


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"dblpcli {__version__}")
        raise typer.Exit()


def output_result(
    data: dict,
    format: OutputFormat,
    data_type: str = "publication",
) -> None:
    """Output data in the specified format."""
    if format == OutputFormat.JSON:
        typer.echo(format_json(data))
    elif format == OutputFormat.BIBTEX:
        # For bibtex format, we need to fetch bibtex for each result
        typer.echo("BibTeX format requires using the 'bibtex' command directly.", err=True)
        raise typer.Exit(1)
    else:
        typer.echo(format_table(data, data_type))


def handle_error(e: DBLPError, format: OutputFormat) -> None:
    """Handle and output an error."""
    if format == OutputFormat.JSON:
        extra = {}
        if isinstance(e, NotFoundError) and e.key:
            extra["key"] = e.key
        typer.echo(format_error_json(e.code or "ERROR", e.message, e.suggestion, **extra))
    else:
        typer.echo(f"Error: {e.message}", err=True)
        if e.suggestion:
            typer.echo(e.suggestion, err=True)
    raise typer.Exit(1)


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", "-v", callback=version_callback, is_eager=True, help="Show version and exit."),
    ] = False,
) -> None:
    """CLI for DBLP, for humans and agents alike."""
    pass


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query (supports AND/OR operators)")],
    limit: Annotated[int, typer.Option("--limit", "-n", help="Maximum number of results")] = 30,
    offset: Annotated[int, typer.Option("--offset", help="Result offset for pagination")] = 0,
    year: Annotated[
        Optional[str], typer.Option("--year", "-y", help="Year or year range (e.g., 2020 or 2020-2024)")
    ] = None,
    venue: Annotated[Optional[str], typer.Option("--venue", help="Filter by venue name")] = None,
    format: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.TABLE,
) -> None:
    """Search publications in DBLP.

    Supports boolean operators AND/OR (case-insensitive) in queries.
    Use "author:Name" to search by author name.

    JSON output fields per result:
      key: DBLP key (use with 'pub' or 'bibtex' commands)
      title, year, authors, venue, type, doi

    Examples:
        dblpcli search "transformer attention"
        dblpcli search "deep learning" --year 2020-2024
        dblpcli search "author:Vaswani" --limit 10
        dblpcli search "neural network AND classification" --format json
    """
    # Build query with filters
    search_query = query

    if year:
        if "-" in year:
            year_from, year_to = year.split("-", 1)
            search_query += f" year:{year_from}:{year_to}"
        else:
            search_query += f" year:{year}:"

    if venue:
        search_query += f" venue:{venue}:"

    try:
        with DBLPClient() as client:
            result = client.search_publications(search_query, limit=limit, offset=offset)
            output_result(result, format, data_type="publication")
    except DBLPError as e:
        handle_error(e, format)


@app.command()
def pub(
    key: Annotated[str, typer.Argument(help="DBLP publication key (e.g., conf/nips/VaswaniSPUJGKP17)")],
    format: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.TABLE,
) -> None:
    """Get a publication by its DBLP key.

    The key can be found in search results or on DBLP website URLs.
    Key format: type/venue/identifier (e.g., conf/nips/VaswaniSPUJGKP17)

    JSON output fields:
      key, title, year, authors, venue, type, doi, pages, volume

    Examples:
        dblpcli pub conf/nips/VaswaniSPUJGKP17
        dblpcli pub journals/corr/abs-1706-03762 --format json
    """
    try:
        with DBLPClient() as client:
            result = client.get_publication(key)
            output_result(result, format, data_type="publication")
    except DBLPError as e:
        handle_error(e, format)


@app.command()
def bibtex(
    keys: Annotated[list[str], typer.Argument(help="One or more DBLP publication keys")],
    key: Annotated[
        Optional[str], typer.Option("--key", "-k", help="Custom citation key (single key only)")
    ] = None,
    output: Annotated[
        Optional[Path], typer.Option("--output", "-o", help="Output file path (.bib added if missing)")
    ] = None,
) -> None:
    """Export BibTeX for publications (fetched directly from DBLP).

    BibTeX is retrieved directly from DBLP, not generated.
    Supports multiple keys for batch export.

    Output: Raw BibTeX text (not JSON). Use --output to save to file.

    Examples:
        dblpcli bibtex conf/nips/VaswaniSPUJGKP17
        dblpcli bibtex conf/nips/VaswaniSPUJGKP17 journals/jmlr/KingmaB14
        dblpcli bibtex conf/nips/VaswaniSPUJGKP17 --key vaswani2017attention
        dblpcli bibtex conf/nips/VaswaniSPUJGKP17 --output refs.bib
    """
    if key and len(keys) > 1:
        typer.echo("Error: --key can only be used with a single publication key", err=True)
        raise typer.Exit(1)

    try:
        with DBLPClient() as client:
            if len(keys) == 1:
                bibtex_str = client.get_publication_bibtex(keys[0])
                # Replace citation key if custom one provided
                if key:
                    # BibTeX entries start with @type{key,
                    import re
                    bibtex_str = re.sub(r'(@\w+\{)[^,]+,', f'\\1{key},', bibtex_str, count=1)
            else:
                bibtex_str = client.get_bibtex_batch(keys)

            if output:
                # Ensure .bib extension
                if not str(output).endswith(".bib"):
                    output = Path(str(output) + ".bib")
                # Create parent directories
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(bibtex_str)
                typer.echo(f"BibTeX written to {output}")
            else:
                typer.echo(bibtex_str)

    except NotFoundError as e:
        typer.echo(f"Error: Publication not found: {e.key or keys}", err=True)
        raise typer.Exit(1)
    except DBLPError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(1)


# Author commands

@author_app.command("search")
def author_search(
    query: Annotated[str, typer.Argument(help="Author name to search for")],
    limit: Annotated[int, typer.Option("--limit", "-n", help="Maximum number of results")] = 30,
    offset: Annotated[int, typer.Option("--offset", help="Result offset for pagination")] = 0,
    format: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.TABLE,
) -> None:
    """Search for authors by name.

    JSON output fields per result:
      pid: Author's persistent identifier (use with 'author get/pubs/bibtex')
      name: Display name
      notes: Affiliations and other info

    Examples:
        dblpcli author search "Geoffrey Hinton"
        dblpcli author search "Hinton" --limit 10 --format json
    """
    try:
        with DBLPClient() as client:
            result = client.search_authors(query, limit=limit, offset=offset)
            output_result(result, format, data_type="author")
    except DBLPError as e:
        handle_error(e, format)


@author_app.command("get")
def author_get(
    pid: Annotated[str, typer.Argument(help="Author PID (e.g., 56/953 or h/GeoffreyEHinton)")],
    format: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.TABLE,
) -> None:
    """Get an author by their PID.

    The PID (persistent identifier) can be found using 'author search'.
    PID formats: numeric (56/953) or name-based (h/GeoffreyEHinton)

    JSON output fields:
      pid, name, publication_count

    Examples:
        dblpcli author get 56/953
        dblpcli author get h/GeoffreyEHinton --format json
    """
    try:
        with DBLPClient() as client:
            result = client.get_author(pid)
            # Format as author detail
            author_info = {
                "pid": result.get("pid", pid),
                "name": result.get("name", ""),
                "publication_count": len(result.get("publications", [])),
            }
            output_result(author_info, format, data_type="author")
    except DBLPError as e:
        handle_error(e, format)


@author_app.command("pubs")
def author_pubs(
    pid: Annotated[str, typer.Argument(help="Author PID (e.g., 56/953 or h/GeoffreyEHinton)")],
    limit: Annotated[Optional[int], typer.Option("--limit", "-n", help="Maximum number of publications")] = None,
    year: Annotated[
        Optional[str], typer.Option("--year", "-y", help="Year or year range (e.g., 2020 or 2020-2024)")
    ] = None,
    format: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.TABLE,
) -> None:
    """Get publications for an author.

    Returns publications sorted by year (newest first).

    JSON output structure:
      author: {name, pid}
      publications: [{key, title, year, authors, venue}, ...]
      meta: {total}

    Examples:
        dblpcli author pubs 56/953
        dblpcli author pubs h/GeoffreyEHinton --year 2020-2024 --limit 50
    """
    year_from = None
    year_to = None
    if year:
        if "-" in year:
            parts = year.split("-", 1)
            year_from = int(parts[0])
            year_to = int(parts[1])
        else:
            year_from = int(year)
            year_to = int(year)

    try:
        with DBLPClient() as client:
            result = client.get_author_publications(pid, limit=limit, year_from=year_from, year_to=year_to)
            output_result(result, format, data_type="publication")
    except DBLPError as e:
        handle_error(e, format)


@author_app.command("bibtex")
def author_bibtex(
    pid: Annotated[str, typer.Argument(help="Author PID (e.g., 56/953 or h/GeoffreyEHinton)")],
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Output file path")] = None,
) -> None:
    """Export BibTeX for all publications of an author.

    BibTeX is fetched directly from DBLP (not generated).

    Examples:
        dblpcli author bibtex 56/953
        dblpcli author bibtex h/GeoffreyEHinton --output hinton.bib
    """
    try:
        with DBLPClient() as client:
            bibtex_str = client.get_author_bibtex(pid)

            if output:
                if not str(output).endswith(".bib"):
                    output = Path(str(output) + ".bib")
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(bibtex_str)
                typer.echo(f"BibTeX written to {output}")
            else:
                typer.echo(bibtex_str)

    except DBLPError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(1)


# Venue commands

@venue_app.command("search")
def venue_search(
    query: Annotated[str, typer.Argument(help="Venue name to search for")],
    limit: Annotated[int, typer.Option("--limit", "-n", help="Maximum number of results")] = 30,
    offset: Annotated[int, typer.Option("--offset", help="Result offset for pagination")] = 0,
    type: Annotated[Optional[str], typer.Option("--type", "-t", help="Venue type filter (conf, journals)")] = None,
    format: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.TABLE,
) -> None:
    """Search for venues (conferences/journals).

    JSON output fields per result:
      key: Venue key (use with 'venue get/pubs', e.g., conf/nips)
      name: Full venue name
      acronym: Short name (e.g., NeurIPS)
      type: Conference, Journal, etc.

    Examples:
        dblpcli venue search "NeurIPS"
        dblpcli venue search "machine learning" --type conf
    """
    search_query = query
    if type:
        search_query += f" type:{type}:"

    try:
        with DBLPClient() as client:
            result = client.search_venues(search_query, limit=limit, offset=offset)
            output_result(result, format, data_type="venue")
    except DBLPError as e:
        handle_error(e, format)


@venue_app.command("get")
def venue_get(
    key: Annotated[str, typer.Argument(help="Venue key (e.g., conf/nips or journals/jmlr)")],
    format: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.TABLE,
) -> None:
    """Get information about a venue.

    Venue key format: type/name (e.g., conf/nips, journals/jmlr)
    Find venue keys using 'venue search'.

    JSON output fields:
      key, name, acronym, type, url

    Examples:
        dblpcli venue get conf/nips
        dblpcli venue get journals/jmlr --format json
    """
    # Search for the venue by key to get its details
    try:
        with DBLPClient() as client:
            # Extract venue name from key for search
            venue_name = key.split("/")[-1]
            result = client.search_venues(venue_name, limit=10)

            # Find matching venue
            for v in result.get("results", []):
                if v.get("key") == key or key in v.get("key", ""):
                    output_result(v, format, data_type="venue")
                    return

            # If no exact match, show search results
            if result.get("results"):
                typer.echo(f"Venue '{key}' not found. Similar venues:", err=True)
                output_result(result, format, data_type="venue")
            else:
                typer.echo(f"Venue not found: {key}", err=True)
                raise typer.Exit(1)

    except DBLPError as e:
        handle_error(e, format)


@venue_app.command("pubs")
def venue_pubs(
    key: Annotated[str, typer.Argument(help="Venue key (e.g., conf/nips or journals/jmlr)")],
    year: Annotated[Optional[int], typer.Option("--year", "-y", help="Filter by specific year")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="Maximum number of results")] = 30,
    offset: Annotated[int, typer.Option("--offset", help="Result offset for pagination")] = 0,
    format: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.TABLE,
) -> None:
    """Get publications from a venue.

    Use --year to filter by a specific year (recommended for large venues).

    JSON output structure:
      results: [{key, title, year, authors, venue}, ...]
      meta: {total, query}

    Examples:
        dblpcli venue pubs conf/nips --year 2023
        dblpcli venue pubs journals/jmlr --limit 50 --format json
    """
    try:
        with DBLPClient() as client:
            result = client.get_venue_publications(key, year=year, limit=limit, offset=offset)
            output_result(result, format, data_type="publication")
    except DBLPError as e:
        handle_error(e, format)


if __name__ == "__main__":
    app()
