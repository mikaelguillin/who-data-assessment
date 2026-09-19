from pipeline.ingest import run_ingest


def main() -> None:
    counts = run_ingest()
    print(
        "Ingest complete: "
        f"{counts['runs']} runs, {counts['expenditures']} expenditures, "
        f"{counts['classifications']} classifications, {counts['flags']} flags"
    )


if __name__ == "__main__":
    main()
