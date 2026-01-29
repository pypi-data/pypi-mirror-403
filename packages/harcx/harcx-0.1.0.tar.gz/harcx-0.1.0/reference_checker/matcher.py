"""Author name matching utilities."""

import re

from rapidfuzz import fuzz


def normalize_author_name(name: str) -> str:
    """Convert various formats to 'firstname lastname' lowercase.

    Handles:
    - "Smith, John" -> "john smith"
    - "J. Smith" -> "j smith"
    - "{van der Berg}, Jan" -> "jan van der berg"
    """
    name = name.strip()

    # Remove braces
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


def get_last_name(name: str) -> str:
    """Extract probable last name from normalized name string."""
    parts = name.split()
    if not parts:
        return ""
    # Last word is usually the last name (after normalization)
    return parts[-1]


def names_match(name1: str, name2: str, threshold: float = 80.0) -> bool:
    """Check if two author names match using fuzzy matching.

    Accounts for:
    - Initials vs full names ("j smith" vs "john smith")
    - Minor spelling variations
    - Missing middle names
    """
    # Check if last names match and first part is compatible
    parts1 = name1.split()
    parts2 = name2.split()

    if not parts1 or not parts2:
        return False

    # Last names should be similar
    last1, last2 = parts1[-1], parts2[-1]
    if fuzz.ratio(last1, last2) < threshold:
        return False

    # If one has initials, check first letter matches
    first1 = parts1[0] if parts1 else ""
    first2 = parts2[0] if parts2 else ""

    # Handle initials (single letter or letter with period)
    is_initial1 = len(first1.replace(".", "")) <= 2
    is_initial2 = len(first2.replace(".", "")) <= 2

    if is_initial1 or is_initial2:
        # Just check first letters match
        if first1 and first2:
            return first1[0] == first2[0]
        return False

    # Both have full first names - require higher threshold to avoid
    # matching similar but different names like "john" vs "jane"
    return fuzz.ratio(first1, first2) >= 85.0


def calculate_author_match(
    bib_authors: list[str], paper_authors: list[str]
) -> float:
    """Return 0.0-1.0 score for author list similarity.

    Uses fuzzy matching to account for:
    - Missing middle names
    - Initials vs full names
    - Minor spelling differences

    Returns ratio of matched authors from the smaller list.
    """
    if not bib_authors or not paper_authors:
        return 0.0

    # Normalize paper authors
    normalized_paper = [normalize_author_name(a) for a in paper_authors]

    # Count matches
    matched = 0
    used_paper_indices = set()

    for bib_author in bib_authors:
        for i, paper_author in enumerate(normalized_paper):
            if i in used_paper_indices:
                continue
            if names_match(bib_author, paper_author):
                matched += 1
                used_paper_indices.add(i)
                break

    # Score based on smaller list to handle partial author lists
    min_count = min(len(bib_authors), len(paper_authors))
    return matched / min_count if min_count > 0 else 0.0
