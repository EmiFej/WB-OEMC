#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEPSO generation mix scraper
===========================
Extracts the **hourly** production of five technology groups published in the
MEPSO daily PDF (“Дневни податоци”):

* **ВКУПНО ХЕЦ**  →  `hec`  (hydro)
* **ВКУПНО ТЕЦ**  →  `tec`  (coal / thermal)
* **ВКУПНО ГАС**  →  `gas`
* **ВКУПНО ВЕЦ**  →  `vec`  (wind)
* **ВКУПНО ФЕЦ**  →  `fec`  (solar/PV)

Key points
~~~~~~~~~~
* Works with both Macedonian and mixed‑punctuation number styles.
* Ignores the daily‑sum column (threshold 500 MWh instead of the 2 000 used
  for total demand).
* Outputs a **wide** CSV with columns:
  `date,hour,hec,tec,gas,vec,fec` (one row = one hour).
* If a row is missing from the PDF the corresponding column stays blank.
"""
from __future__ import annotations
import os, re, logging, unicodedata, requests, pdfplumber, pandas as pd, yaml
from io import BytesIO
from datetime import datetime, timedelta
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from pdfplumber.utils.exceptions import PdfminerException
from pdfminer.high_level import extract_text as pdfminer_text
from tqdm import tqdm

logging.getLogger("pdfminer").setLevel(logging.ERROR)
BASE_DIR = "https://www.mepso.com.mk/files/mk/dnevni"

# ───────────── targets & regex helpers ──────────────────────────────────
TARGET_LABELS = {
    "вкупно хец": "Hydro",
    "вкупно тец": "Thermal",
    "вкупно гас": "Natural_gas",
    "вкупно вец": "Wind_power",
    "вкупно фец": "Solar_power",
}
LABEL_PAT = re.compile("|".join(re.escape(k) for k in TARGET_LABELS), re.I)

SPACE    = r"[ \u00A0\u202F]"
TOKEN_RE = re.compile(r"\d{1,3}(?:[.,\u00A0\u202F ]\d{3})*[.,]\d+")
SUM_THRES = 500                     # anything above → daily total, not hour

# ───────────── number normaliser ────────────────────────────────────────

def normalise(tok: str) -> float:
    """Return **tok**→float no matter whether “1,234.5” or “1.234,5”."""
    tok = re.sub(SPACE, "", tok)
    if "," in tok and "." in tok:
        pos = max(tok.rfind(","), tok.rfind("."))
        tok = tok[:pos].replace(",", "").replace(".", "") + "." + tok[pos + 1 :]
    else:
        tok = tok.replace(",", ".")
    return float(tok)

# ───────────── possible filenames for a given day ───────────────────────

def url_variants(day: datetime) -> list[str]:
    dmy, yy = day.strftime("%d.%m.%Y"), day.strftime("%y%m%d")
    return [
        f"{BASE_DIR}/{quote(f'Информација за {dmy}.pdf')}",
        f"{BASE_DIR}/{quote(f'Информација {dmy}.pdf')}",
        f"{BASE_DIR}/{quote(f'WebReport-{yy}_mk.pdf')}",
    ]

# ───────────── helpers to clean a row into 24 hours ─────────────────────

def clean_cells(cells: list[str | None]) -> list[float | None] | None:
    """Convert the *data* part of a PDF row to 24 hourly floats/None."""
    # drop trailing empties some tables have
    while cells and not cells[-1]:
        cells.pop()

    numeric = [c for c in cells if c and re.search(r"\d", c)]
    if not numeric:
        return None

    if len(numeric) > 24 or normalise(numeric[0]) > SUM_THRES:
        numeric = numeric[1:]            # discard daily sum

    if len(numeric) < 24:
        numeric.extend([None] * (24 - len(numeric)))
    elif len(numeric) > 24:
        numeric = numeric[-24:]          # keep last 24 numbers

    if len(numeric) != 24:
        return None

    try:
        return [None if v is None else normalise(v) for v in numeric]
    except Exception:
        return None

# ───────────── table‑mode extractor ─────────────────────────────────────

def extract_via_table(raw: bytes) -> dict[str, list[float | None]] | None:
    found: dict[str, list[float | None]] = {}
    try:
        with pdfplumber.open(BytesIO(raw)) as pdf:
            page  = pdf.pages[0]
            table = page.extract_table({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
            })
    except PdfminerException:
        return None

    if not table:
        return None

    for row in table:
        if not row or not row[0]:
            continue
        label_txt = unicodedata.normalize("NFKC", row[0]).lower()
        for match, colname in TARGET_LABELS.items():
            if match in label_txt:
                vals = clean_cells(row[1:])
                if vals:
                    found[colname] = vals
                break
    return found or None

# ───────────── regex fallback ───────────────────────────────────────────

def extract_via_regex(raw: bytes) -> dict[str, list[float | None]] | None:
    try:
        with pdfplumber.open(BytesIO(raw)) as pdf:
            txt = "\n".join(p.extract_text() or "" for p in pdf.pages)
    except PdfminerException:
        txt = ""
    if not txt.strip():
        try:
            txt = pdfminer_text(BytesIO(raw))
        except Exception:
            txt = ""

    txt = unicodedata.normalize("NFKC", txt).lower()
    found: dict[str, list[float | None]] = {}
    for line in txt.splitlines():
        if not LABEL_PAT.search(line):
            continue
        for match, colname in TARGET_LABELS.items():
            if match in line:
                tokens = TOKEN_RE.findall(line)
                if not tokens:
                    continue
                vals = [normalise(t) for t in tokens]
                if len(vals) > 24 or vals[0] > SUM_THRES:
                    vals = vals[1:]
                if len(vals) < 24:
                    vals.extend([None] * (24 - len(vals)))
                elif len(vals) > 24:
                    vals = vals[-24:]
                if len(vals) == 24:
                    found[colname] = vals
    return found or None

# ───────────── per‑day worker ───────────────────────────────────────────

def fetch_day(day: datetime, out_dir: str) -> list[dict]:
    for url in url_variants(day):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            raw  = resp.content
            data = extract_via_table(raw) or extract_via_regex(raw)
            if data:
                rows: list[dict] = []
                # guarantee all tech columns exist, filled with None if absent
                for h in range(24):
                    row = {
                        "date": day.strftime("%Y-%m-%d"),
                        "hour": h + 1,
                        **{col: data.get(col, [None] * 24)[h] for col in TARGET_LABELS.values()},
                    }
                    rows.append(row)
                return rows
            # stash raw if nothing parsed
            fname = os.path.join(out_dir, f"mepso_{day:%Y-%m-%d}_unparsed.pdf" if raw[:4] == b"%PDF" else f"mepso_{day:%Y-%m-%d}_unparsed.bin")
            if not os.path.exists(fname):
                with open(fname, "wb") as fp:
                    fp.write(raw)
        except Exception as exc:
            logging.debug("MEPSO error [%s]: %s", url, exc)
    return []

# ───────────── main entry ───────────────────────────────────────────────

def run(overwrite: bool = False) -> None:
    cfg = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "..", "config.yaml"), encoding="utf-8"))
    start = datetime.strptime(cfg["START_DATE"], "%Y-%m-%d")
    end   = datetime.strptime(cfg["END_DATE"], "%Y-%m-%d")
    out_dir, workers = cfg["OUTPUT_DIR"], int(cfg["MAX_WORKERS"])
    os.makedirs(out_dir, exist_ok=True)

    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_day, d, out_dir): d for d in days}
        for fut in tqdm(as_completed(futures), total=len(futures), unit="day"):
            rows.extend(fut.result())

    # dense grid so missing hours appear blank
    skel = pd.MultiIndex.from_product(
        [pd.date_range(start, end).strftime("%Y-%m-%d"), range(1, 25)],
        names=["date", "hour"],
    ).to_frame(index=False)
    real = pd.DataFrame(rows)  # already wide
    df   = skel.merge(real, how="left", on=["date", "hour"]).sort_values(["date", "hour"])

    out_path = os.path.join(out_dir, "mepso_gen_mix.csv")
    df.to_csv(out_path, index=False, na_rep="")
    print(
        f"✅ MEPSO generation mix saved to {out_path} "
        f"({df['date'].nunique()} days, {sum(df[c].count() for c in TARGET_LABELS.values())} hourly values)"
    )

if __name__ == "__main__":
    run()
