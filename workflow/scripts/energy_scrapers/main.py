#!/usr/bin/env python3
"""
Central dispatcher for the energy-scraper suite.

Targets
-------
mepso        – hourly demand (existing)
mepso_gen    – generation mix by technology (NEW)
ost          – OST demand (existing)
nosbih       – NOSBiH demand (existing)
all          – run every target above
"""
import argparse

# demand scrapers (already present)
from energy_scrapers import (
    download_mepso,
    download_ost,
    download_nosbih,
)

# generation-mix scraper (new module you added as *mepso_gen_scraper.py*)
import energy_scrapers.mepso_gen_scraper as download_mepso_gen


def main() -> None:
    parser = argparse.ArgumentParser(description="Energy Data Downloader")
    parser.add_argument(
        "--target",
        type=str,
        choices=["mepso", "mepso_gen", "ost", "nosbih", "all"],
        required=True,
        help="Dataset to download",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing files"
    )
    args = parser.parse_args()

    if args.target in ("mepso", "all"):
        download_mepso.run(overwrite=args.overwrite)

    if args.target in ("mepso_gen", "all"):
        download_mepso_gen.run(overwrite=args.overwrite)

    if args.target in ("ost", "all"):
        download_ost.run(overwrite=args.overwrite)

    if args.target in ("nosbih", "all"):
        download_nosbih.run(overwrite=args.overwrite)


if __name__ == "__main__":
    main()
