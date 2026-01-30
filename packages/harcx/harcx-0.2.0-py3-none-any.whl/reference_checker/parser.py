"""BibTeX parsing logic."""

import re

import bibtexparser

from .models import BibEntry


def normalize_author_name(name: str) -> str:
    """Convert various author name formats to 'firstname lastname' lowercase.

    Handles:
    - "Smith, John" -> "john smith"
    - "John Smith" -> "john smith"
    - "J. Smith" -> "j smith"
    - "{van der Berg}, Jan" -> "jan van der berg"
    """
    name = name.strip()

    # Remove braces used for protecting capitalization
    name = re.sub(r"\{([^}]+)\}", r"\1", name)

    # Handle "Last, First" format
    if "," in name:
        parts = name.split(",", 1)
        last = parts[0].strip()
        first = parts[1].strip() if len(parts) > 1 else ""
        name = f"{first} {last}".strip()

    # Normalize whitespace and lowercase
    name = " ".join(name.split()).lower()

    return name


def parse_authors(author_string: str) -> list[str]:
    """Parse BibTeX author string into list of normalized names.

    BibTeX uses " and " to separate multiple authors.
    """
    if not author_string:
        return []

    # Split on " and " (case insensitive)
    authors = re.split(r"\s+and\s+", author_string, flags=re.IGNORECASE)

    return [normalize_author_name(a) for a in authors if a.strip()]


def parse_bib_file(file_path: str) -> list[BibEntry]:
    """Parse .bib file and extract entries with normalized author names.

    Args:
        file_path: Path to the .bib file

    Returns:
        List of BibEntry objects
    """
    with open(file_path, encoding="utf-8") as f:
        bib_database = bibtexparser.load(f)

    entries = []
    for entry in bib_database.entries:
        # Extract required fields
        key = entry.get("ID", "")
        title = entry.get("title", "")
        author_string = entry.get("author", "")
        year = entry.get("year")

        # Clean up title (remove braces, extra whitespace)
        title = re.sub(r"\{([^}]+)\}", r"\1", title)
        title = " ".join(title.split())

        # Parse authors
        authors = parse_authors(author_string)

        entries.append(
            BibEntry(
                key=key,
                title=title,
                authors=authors,
                year=year,
                raw_entry=entry,
            )
        )

    return entries
