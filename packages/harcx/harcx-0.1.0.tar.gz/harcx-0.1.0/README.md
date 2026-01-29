# HaRC - Hallucinated Reference Checker

A Python library to verify BibTeX entries against Semantic Scholar. Identify citations in your `.bib` files that may be incorrect, misspelled, or don't exist in the academic literature.

## Installation

```bash
uv sync
```

## Quick Start

### Python API

```python
from reference_checker import check_citations

# Check a .bib file - returns entries that weren't found/verified
not_found = check_citations("references.bib")

for result in not_found:
    print(f"{result.entry.key}: {result.message}")
```

### Command Line

```bash
# Basic usage
uv run harc references.bib

# With verbose output
uv run harc references.bib --verbose

# Custom author match threshold
uv run harc references.bib --threshold 0.7

# With Semantic Scholar API key (for higher rate limits)
uv run harc references.bib --api-key YOUR_API_KEY
```

## How It Works

1. **Parse** - Reads your `.bib` file and extracts entries with normalized author names
2. **Search** - Queries Semantic Scholar for each paper by title
3. **Match** - Compares authors using fuzzy matching to handle name variations
4. **Report** - Returns entries that couldn't be verified

A paper is considered "found" when:
- Semantic Scholar returns a result for the title
- Author match score meets the threshold (default: 60%)
- Year matches within tolerance (default: ±1 year)

## API Reference

### `check_citations()`

```python
def check_citations(
    bib_file: str,
    author_threshold: float = 0.6,
    year_tolerance: int = 1,
    api_key: str | None = None,
    verbose: bool = False,
) -> list[CheckResult]:
```

**Parameters:**
- `bib_file` - Path to the `.bib` file
- `author_threshold` - Minimum author match score (0.0-1.0) to consider verified
- `year_tolerance` - Allowed year difference between bib entry and found paper
- `api_key` - Optional Semantic Scholar API key for higher rate limits
- `verbose` - Print progress information

**Returns:** List of `CheckResult` objects for entries that were NOT found/verified.

### `CheckResult`

```python
@dataclass
class CheckResult:
    entry: BibEntry           # The original bib entry
    found: bool               # Whether the paper was verified
    matched_paper: dict | None  # Semantic Scholar data if found
    author_match_score: float # 0.0-1.0 confidence score
    message: str              # Human-readable status
```

### `BibEntry`

```python
@dataclass
class BibEntry:
    key: str              # BibTeX key (e.g., "smith2023")
    title: str            # Paper title
    authors: list[str]    # Normalized author names
    year: str | None      # Publication year
    raw_entry: dict       # Original bibtexparser dict
```

## Author Matching

The library handles common author name variations:

- **Last, First** format: `"Smith, John"` → `"john smith"`
- **First Last** format: `"John Smith"` → `"john smith"`
- **Initials**: `"J. Smith"` matches `"John Smith"`
- **Protected names**: `"{van der Berg}, Jan"` → `"jan van der berg"`

Fuzzy matching accounts for minor spelling differences and missing middle names.

## Rate Limiting

Semantic Scholar has rate limits for API access:

- **Unauthenticated**: Shared pool, may experience throttling
- **Authenticated**: Higher limits with API key

The library includes:
- Automatic delay between requests (3 seconds default)
- Exponential backoff on rate limit errors
- Up to 3 retries per request

For production use, [request an API key](https://www.semanticscholar.org/product/api) from Semantic Scholar.

## Development

### Run Tests

```bash
uv sync --extra dev
uv run pytest tests/ -v
```

### Project Structure

```
reference_checker/
├── __init__.py      # Main API
├── models.py        # Data classes
├── parser.py        # BibTeX parsing
├── matcher.py       # Author name matching
├── scholar.py       # Semantic Scholar client
└── cli.py           # Command-line interface
```

## License

MIT
