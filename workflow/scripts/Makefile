###############################################################################
# Makefile –  make      → venv + editable install + Snakemake
#             make clean→ wipe venv + artefacts + data
###############################################################################

PYTHON ?= python3          # override with  make PYTHON=python
VENV   := .venv            # DO NOT leave trailing spaces here!
SNAKEFILE := snakefile     # rename to Snakefile if you wish

# helper paths
PY  := $(strip $(VENV))/bin/$(PYTHON)
PIP := $(strip $(VENV))/bin/pip

# default goal ---------------------------------------------------------------
all: venv install deps scrape

# 1) venv --------------------------------------------------------------------
$(VENV):
	$(PYTHON) -m venv $@

venv: | $(VENV)

# 2) editable install --------------------------------------------------------
install: venv setup.py
	$(PIP) install --upgrade pip
	$(PIP) install -e .

# 3) dependencies ------------------------------------------------------------
deps: venv requirements.txt
	$(PIP) install -r requirements.txt
	$(PIP) install snakemake          # or add to requirements.txt instead

# 4) run the pipeline --------------------------------------------------------
scrape:
	$(PY) -m snakemake -j 1 -s $(SNAKEFILE)

# housekeeping ---------------------------------------------------------------
clean:
	rm -rf $(strip $(VENV))/ .snakemake build dist *.egg-info data_scraping data/*.csv || true

.PHONY: all venv install deps scrape clean
###############################################################################
