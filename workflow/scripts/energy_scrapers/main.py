#!/usr/bin/env python3
"""
Central dispatcher for the energy-scraper suite.

Targets
-------
mepso        – hourly demand (existing)
mepso_gen    – generation mix by technology (NEW)
ost          – OST demand (existing)
nosbih       – NOSBiH demand (existing)
albania_checks – Albania validation checks (NEW)
all          – run every target above
"""
import argparse

# demand scrapers (already present)
from . import (
    download_mepso,
    download_ost,
    download_nosbih,
)

# generation-mix scraper (new module you added as *mepso_gen_scraper.py*)
from . import mepso_gen_scraper as download_mepso_gen

# Albania validation checks
from . import albania_checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Energy Data Downloader")
    parser.add_argument(
        "--target",
        type=str,
        choices=["mepso", "mepso_gen", "ost", "nosbih", "albania_checks", "all"],
        required=True,
        help="Dataset to download or checks to run",
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

    if args.target in ("albania_checks", "all"):
        # Run Albania validation checks
        import os
        ost_data_path = "../../data/energy_scrapers/ost_demand.csv"
        if os.path.exists(ost_data_path):
            results = albania_checks.run_albania_checks(ost_data_path)
        else:
            results = albania_checks.run_albania_checks()
        albania_checks.print_check_results(results)


if __name__ == "__main__":
    main()
