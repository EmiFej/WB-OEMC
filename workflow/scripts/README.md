# Energy Scrapers

This is a collection of scrapers for downloading power sector data from various sources, including:
- The Albanian TSO (**OST**)
- The North Macedonian TSO (**MEPSO**)
- The TSO of Bosnia and Herzegovina (**NOSBiH**)

### After cloning the repository, navigate to energy-scrapers

cd workflow/scripts/energy-scrapers

### If you have an active conda environment (even when in 'Base')

conda deactivate

## Run 'make' (create venv + editable install + dependencies + run DAG)

make

### What 'make' does (see Makefile for more details):
venv – python3 -m venv .venv

install – pip install -e . (editable package energy_scrapers)

deps – pip install -r requirements.txt + snakemake

scrape – snakemake -s snakefile … (builds every CSV listed in rule all)

## Configuring your run window
### Edit config.yaml:
START_DATE: "2025-01-01"<br/>
END_DATE: "2025-04-25"<br/>
OUTPUT_DIR: "data"<br/>
OVERWRITE:   false      # true = ignore cached CSVs<br/>
MAX_WORKERS: 10         # thread pool size. WARNING: Increasing this value could lead to failed downloads for certain dates.

# 📁 Energy Scrapers layout

```text
.
├── config.yaml                 # start/end dates, OUTPUT_DIR, etc.
├── requirements.txt            # run-time deps (pdfplumber, requests…)
├── setup.py                    # pip-installable package metadata
├── snakefile                   # Snakemake DAG (MEPSO, OST, NOSBiH…)
├── Makefile                    # convenience shortcuts (venv, scrape, …)
├── scripts
│   └── energy_scrapers
│       ├── __init__.py
│       ├── main.py             # CLI dispatcher --target <name>
│       ├── mepso_demand_scraper.py
│       ├── mepso_gen_scraper.py
│       ├── download_ost.py
│       ├── download_nosbih.py
│       └── …                   # add new scrapers here
├── data                        # created automatically after “make”
│   ├── mepso_data.csv
│   ├── mepso_gen_mix.csv
│   ├── ost_data.csv
│   └── nosbih_data.csv
└── .venv                       # virtual environment (created by make)


