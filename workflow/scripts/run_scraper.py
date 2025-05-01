# run_scraper.py

import argparse
from energy_scrapers import download_mepso, download_ost, download_nosbih

SCRAPER_MAP = {
    "mepso": download_mepso.run,
    "ost": download_ost.run,
    "nosbih": download_nosbih.run,
}

def main():
    parser = argparse.ArgumentParser(description="Energy data scraper bundle.")
    parser.add_argument(
        "sources",
        nargs="+",
        choices=SCRAPER_MAP.keys(),
        help="Which sources to download (choose one or more: mepso, ost, nosbih)."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Force re-download even if files exist."
    )

    args = parser.parse_args()

    for source in args.sources:
        print(f"🔵 Running scraper for {source.upper()}...")
        SCRAPER_MAP[source](overwrite=args.overwrite)

if __name__ == "__main__":
    main()

''' Example CLI usage: # Download only MEPSO
python run_scraper.py mepso

# Download MEPSO and NOSBiH
python run_scraper.py mepso nosbih

# Redownload everything with --overwrite
python run_scraper.py mepso ost nosbih --overwrite
'''