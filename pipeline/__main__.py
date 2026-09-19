import argparse
from pathlib import Path

from pipeline.adapters.base import UnsupportedLayoutError
from pipeline.ingest import run_ingest


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a country expenditure extract into the review store")
    parser.add_argument("--file", required=True, type=Path, help="CSV, Excel (.xlsx), or JSON extract")
    parser.add_argument("--country-name", required=True, help="Display name for the country")
    parser.add_argument("--country-code", help="Optional short code; re-using a code replaces that country")
    parser.add_argument("--flag-emoji", help="Optional country flag emoji, e.g. 🇰🇪")
    args = parser.parse_args()
    if not args.file.is_file():
        parser.error(f"File not found: {args.file}")
    try:
        outcome = run_ingest(
            args.file,
            args.country_name,
            args.country_code,
            flag_emoji=args.flag_emoji,
        )
    except (UnsupportedLayoutError, ValueError) as exc:
        parser.error(str(exc))
    action = "Replaced" if outcome.replaced else "Ingested"
    label = outcome.country_name
    if outcome.flag_emoji:
        label = f"{outcome.flag_emoji} {label}"
    print(
        f"{action} {label} ({outcome.country_code}): "
        f"{outcome.record_count} expenditures, {outcome.classification_count} classifications, "
        f"{outcome.flag_count} flags ({outcome.source_format})"
    )


if __name__ == "__main__":
    main()
