#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEPSO hourly demand scraper
==========================
Covers both Macedonian and English row labels, both punctuation styles and
occasional layout glitches (missing daily‑sum column or even one missing
hour).  Produces a dense `mepso_data.csv` grid (date × hour).
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

# ───────────── regex helpers ────────────────────────────────────────────
SPACE     = r"[ \u00A0\u202F]"  # space / NBSP / NNBSP
TOKEN_RE  = re.compile(r"\d{1,3}(?:[.,\u00A0\u202F ]\d{3})*[.,]\d+")
LABEL_RE  = re.compile(r"(?:вкупен\s*конзум|total\s*consumption)", re.I)
SUM_THRES = 2_000                    # anything above → surely daily sum

# ───────────── punctuation normaliser ───────────────────────────────────

def normalise(tok: str) -> float:
    """Return *tok* as float regardless of ,/. placement."""
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

# ───────────── table‑mode extractor ─────────────────────────────────────

def extract_via_table(raw: bytes) -> list[float | None] | None:
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

    # try to locate the row by label text; fallback to "third‑from‑bottom"
    row: list[str | None] | None = None
    for r in table:
        if r and r[0] and LABEL_RE.search(unicodedata.normalize("NFKC", r[0])):
            row = r
            break
    if not row and len(table) >= 3:
        row = table[-3]
    if not row:
        return None

    cells = row[1:]  # drop label (keep blanks)
    # strip possible trailing blank columns that some PDFs add
    while cells and not cells[-1]:
        cells.pop()

    # we ignore positional blanks – squeeze to numeric tokens
    numeric = [c for c in cells if c and re.search(r"\d", c)]
    if not numeric:
        return None

    # if first token looks like a daily sum, drop it
    if len(numeric) > 24 or normalise(numeric[0]) > SUM_THRES:
        numeric = numeric[1:]

    # pad if MEPSO omitted one hour (rare daylight‑saving glitch)
    if len(numeric) < 24:
        numeric.extend([None] * (24 - len(numeric)))
    elif len(numeric) > 24:               # take the *last* 24 hourly numbers
        numeric = numeric[-24:]

    if len(numeric) != 24:
        return None

    try:
        return [None if v is None else normalise(v) for v in numeric]
    except Exception:
        return None

# ───────────── regex fallback ───────────────────────────────────────────

def extract_via_regex(raw: bytes) -> list[float | None] | None:
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

    txt = unicodedata.normalize("NFKC", txt)
    for line in txt.splitlines():
        if not LABEL_RE.search(line):
            continue
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
            return vals
    return None

# ───────────── per‑day worker ───────────────────────────────────────────

def fetch_day(day: datetime, out_dir: str) -> list[dict]:
    for url in url_variants(day):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            raw  = resp.content
            vals = extract_via_table(raw) or extract_via_regex(raw)
            if vals:
                return [{"date": day.strftime("%Y-%m-%d"), "hour": h + 1, "demand": v} for h, v in enumerate(vals)]
            # stash for manual inspection
            ext  = "pdf" if raw[:4] == b"%PDF" else "bin"
            fname = os.path.join(out_dir, f"mepso_{day:%Y-%m-%d}_unparsed.{ext}")
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

    skel = pd.MultiIndex.from_product([pd.date_range(start, end).strftime("%Y-%m-%d"), range(1, 25)], names=["date", "hour"]).to_frame(index=False)
    real = pd.DataFrame(rows, columns=["date", "hour", "demand"])
    df   = skel.merge(real, how="left", on=["date", "hour"]).sort_values(["date", "hour"])

    out_path = os.path.join(out_dir, "mepso_data.csv")
    df.to_csv(out_path, index=False, na_rep="")
    print(f"✅ MEPSO data saved to {out_path} ({df['date'].nunique()} days, {df['demand'].count()} hourly values)")

if __name__ == "__main__":
    run()
