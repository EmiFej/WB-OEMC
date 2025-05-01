# setup.py  ── editable package definition for:  pip install -e .

from pathlib import Path
from setuptools import setup, find_packages

HERE   = Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf-8")
REQS   = (HERE / "requirements.txt").read_text().splitlines()

setup(
    name="energy-scrapers",
    version="0.1.1",
    description="Energy demand scrapers for MEPSO, OST and NOSBiH",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Emir Fejzic",
    author_email="fejzic@kth.se",
    url="https://github.com/your-username/energy-scrapers",
    packages=find_packages(),          # auto-discovers energy_scrapers/*
    python_requires=">=3.9",
    install_requires=REQS,             # single source of truth
    entry_points={                     # creates a shell command
        "console_scripts": [
            "energy-scrapers=run_scraper:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
