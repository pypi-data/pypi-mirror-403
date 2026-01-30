"""Command-line interface for HaRC reference checker."""

import argparse
import sys

from . import check_citations, check_web_citations


def main() -> int:
    """CLI entry point for HaRC."""
    parser = argparse.ArgumentParser(
        prog="harcx",
        description="Verify .bib file entries against academic databases (Semantic Scholar, DBLP, Google Scholar, Open Library)",
    )
    parser.add_argument(
        "bib_file",
        help="Path to .bib file to check",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress information (verbose by default)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.6,
        help="Minimum author match score (0.0-1.0, default: 0.6)",
    )
    parser.add_argument(
        "--api-key",
        help="Semantic Scholar API key for higher rate limits",
    )
    parser.add_argument(
        "--check-urls",
        action="store_true",
        help="Also check URL citations for reachability and title match",
    )
    parser.add_argument(
        "--title-threshold",
        type=float,
        default=0.6,
        help="Minimum title match score for URL citations (0.0-1.0, default: 0.6)",
    )

    args = parser.parse_args()

    try:
        not_found = check_citations(
            args.bib_file,
            author_threshold=args.threshold,
            api_key=args.api_key,
            verbose=not args.quiet,
        )
    except FileNotFoundError:
        print(f"Error: File not found: {args.bib_file}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Check web citations if requested
    web_issues = []
    if args.check_urls:
        if not args.quiet:
            print(f"\n{'=' * 60}")
            print("Checking URL citations...")
            print("=" * 60)
        try:
            web_issues = check_web_citations(
                args.bib_file,
                title_threshold=args.title_threshold,
                verbose=not args.quiet,
            )
        except Exception as e:
            print(f"Error checking URLs: {e}", file=sys.stderr)

    # Print citation verification summary
    if not_found:
        print(f"\n{'=' * 60}")
        print(f"Found {len(not_found)} entries requiring attention:")
        print("=" * 60)
        for result in not_found:
            print(f"\n[{result.entry.key}]")
            print(f"  Title: {result.entry.title}")
            print(f"  Bib Authors: {', '.join(result.entry.authors)}")
            if result.entry.year:
                print(f"  Year: {result.entry.year}")
            print(f"  Issue: {result.message}")
            # Show URL if available for manual checking
            url = result.entry.raw_entry.get("url")
            if url:
                print(f"  URL: {url}")
    else:
        print("\nAll entries verified successfully!")

    # Print web check summary
    if args.check_urls:
        if web_issues:
            print(f"\n{'=' * 60}")
            print(f"Found {len(web_issues)} URL issues:")
            print("=" * 60)
            for result in web_issues:
                print(f"\n[{result.entry.key}]")
                print(f"  URL: {result.url}")
                if not result.reachable:
                    print(f"  Issue: URL unreachable ({result.message})")
                else:
                    print(f"  Issue: URL works but title doesn't match")
                    print(f"  Expected: {result.entry.title[:60]}...")
                    if result.page_title:
                        print(f"  Found: {result.page_title[:60]}...")
                    print(f"  Match Score: {result.title_match_score:.2f}")
        else:
            print("\nAll URL citations checked successfully!")

    has_issues = bool(not_found) or bool(web_issues)
    return 0 if not has_issues else 1


if __name__ == "__main__":
    sys.exit(main())
