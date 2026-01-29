"""Rich table output formatter."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table


def _truncate(text: str, max_length: int = 60) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def _format_authors(authors: list[str], max_length: int = 30) -> str:
    """Format author list, truncating if needed."""
    if not authors:
        return ""
    if len(authors) == 1:
        return _truncate(authors[0], max_length)
    if len(authors) == 2:
        text = f"{authors[0]} and {authors[1]}"
        return _truncate(text, max_length)
    return _truncate(f"{authors[0]} et al.", max_length)


def format_publications_table(
    publications: list[dict[str, Any]],
    meta: dict[str, Any] | None = None,
) -> str:
    """Format publications as a Rich table."""
    console = Console(force_terminal=True, width=120)

    table = Table(show_header=True, header_style="bold")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Year", justify="right", style="green", no_wrap=True)
    table.add_column("Title")
    table.add_column("Authors", no_wrap=True)

    for pub in publications:
        table.add_row(
            pub.get("key", ""),
            str(pub.get("year", "")),
            pub.get("title", ""),
            _format_authors(pub.get("authors", [])),
        )

    with console.capture() as capture:
        console.print(table)

        if meta:
            total = meta.get("total", len(publications))
            offset = meta.get("offset", 0)
            limit = meta.get("limit", len(publications))
            if total > limit:
                console.print(f"Showing {offset + 1}-{offset + len(publications)} of {total} results")

    return capture.get()


def format_authors_table(
    authors: list[dict[str, Any]],
    meta: dict[str, Any] | None = None,
) -> str:
    """Format authors as a Rich table."""
    console = Console(force_terminal=True, width=120)

    table = Table(show_header=True, header_style="bold")
    table.add_column("PID", style="cyan", no_wrap=True, max_width=25)
    table.add_column("Name", max_width=40)
    table.add_column("Notes", max_width=50)

    for author in authors:
        notes = author.get("notes", [])
        notes_str = ", ".join(notes[:2]) if notes else ""
        table.add_row(
            author.get("pid", ""),
            _truncate(author.get("name", ""), 40),
            _truncate(notes_str, 50),
        )

    with console.capture() as capture:
        console.print(table)

        if meta:
            total = meta.get("total", len(authors))
            offset = meta.get("offset", 0)
            if total > len(authors):
                console.print(f"Showing {offset + 1}-{offset + len(authors)} of {total} results")

    return capture.get()


def format_venues_table(
    venues: list[dict[str, Any]],
    meta: dict[str, Any] | None = None,
) -> str:
    """Format venues as a Rich table."""
    console = Console(force_terminal=True, width=120)

    table = Table(show_header=True, header_style="bold")
    table.add_column("Key", style="cyan", no_wrap=True, max_width=25)
    table.add_column("Acronym", max_width=15)
    table.add_column("Name", max_width=50)
    table.add_column("Type", max_width=15)

    for venue in venues:
        table.add_row(
            venue.get("key", ""),
            venue.get("acronym", ""),
            _truncate(venue.get("name", ""), 50),
            venue.get("type", ""),
        )

    with console.capture() as capture:
        console.print(table)

        if meta:
            total = meta.get("total", len(venues))
            offset = meta.get("offset", 0)
            if total > len(venues):
                console.print(f"Showing {offset + 1}-{offset + len(venues)} of {total} results")

    return capture.get()


def format_publication_detail(pub: dict[str, Any]) -> str:
    """Format a single publication in detail."""
    console = Console(force_terminal=True, width=120)

    with console.capture() as capture:
        console.print(f"[bold cyan]Key:[/] {pub.get('key', '')}")
        console.print(f"[bold]Title:[/] {pub.get('title', '')}")
        if pub.get("authors"):
            console.print(f"[bold]Authors:[/] {', '.join(pub['authors'])}")
        if pub.get("year"):
            console.print(f"[bold]Year:[/] {pub['year']}")
        if pub.get("venue"):
            console.print(f"[bold]Venue:[/] {pub['venue']}")
        if pub.get("type"):
            console.print(f"[bold]Type:[/] {pub['type']}")
        if pub.get("doi"):
            console.print(f"[bold]DOI:[/] {pub['doi']}")
        if pub.get("url"):
            console.print(f"[bold]URL:[/] {pub['url']}")

    return capture.get()


def format_author_detail(author: dict[str, Any]) -> str:
    """Format an author in detail."""
    console = Console(force_terminal=True, width=120)

    with console.capture() as capture:
        console.print(f"[bold cyan]PID:[/] {author.get('pid', '')}")
        console.print(f"[bold]Name:[/] {author.get('name', '')}")
        if author.get("url"):
            console.print(f"[bold]URL:[/] {author['url']}")
        if author.get("notes"):
            console.print(f"[bold]Notes:[/] {', '.join(author['notes'])}")

    return capture.get()


def format_venue_detail(venue: dict[str, Any]) -> str:
    """Format a venue in detail."""
    console = Console(force_terminal=True, width=120)

    with console.capture() as capture:
        console.print(f"[bold cyan]Key:[/] {venue.get('key', '')}")
        console.print(f"[bold]Name:[/] {venue.get('name', '')}")
        if venue.get("acronym"):
            console.print(f"[bold]Acronym:[/] {venue['acronym']}")
        if venue.get("type"):
            console.print(f"[bold]Type:[/] {venue['type']}")
        if venue.get("url"):
            console.print(f"[bold]URL:[/] {venue['url']}")

    return capture.get()


def format_table(
    data: dict[str, Any] | list[Any],
    data_type: str = "publication",
) -> str:
    """Format data as a table based on type.

    Args:
        data: The data to format
        data_type: One of "publication", "author", "venue"

    Returns:
        Formatted table string
    """
    # Handle structured responses
    if isinstance(data, dict):
        if "results" in data:
            items = data["results"]
            meta = data.get("meta")
        elif "publications" in data:
            items = data["publications"]
            meta = data.get("meta")
        else:
            # Single item detail
            if data_type == "publication":
                return format_publication_detail(data)
            elif data_type == "author":
                return format_author_detail(data)
            elif data_type == "venue":
                return format_venue_detail(data)
            else:
                return format_publication_detail(data)
    else:
        items = data
        meta = None

    if not items:
        return "No results found."

    if data_type == "publication":
        return format_publications_table(items, meta)
    elif data_type == "author":
        return format_authors_table(items, meta)
    elif data_type == "venue":
        return format_venues_table(items, meta)
    else:
        return format_publications_table(items, meta)
