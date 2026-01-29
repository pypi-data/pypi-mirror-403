"""Command line interface for Japanese prefecture converter."""

import argparse
import sys

from jp_prefectures_simple import code2name, name2code


def main() -> None:
    """Run the command line interface."""
    parser = argparse.ArgumentParser(
        description="Japanese prefecture names and JIS X 0401 codes converter.",
    )
    parser.add_argument("query", help="Prefecture name or JIS X 0401 code to convert.")

    args = parser.parse_args()

    try:
        # Try as code first (if it looks like a number or 2-digit string)
        if args.query.isdigit() and len(args.query) <= 2:  # noqa: PLR2004
            print(code2name(args.query))  # noqa: T201
        else:
            # Try as name
            print(name2code(args.query))  # noqa: T201
    except (KeyError, ValueError, TypeError) as e:
        print(f"Error: Could not convert '{args.query}'. {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)


if __name__ == "__main__":
    main()
