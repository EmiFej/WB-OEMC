#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download hourly demand data from OST (Albanian TSO).

• Looks in both month folders (current month and the following one).
• Tries every suffix in SUFFIXES – now includes
  '', -1, -2, -3, -4, -001, -002, -003
  to catch files like “…14.04.2025-002.xlsx”.
• Uses cell C158 of each workbook to determine the *true* reporting date.
• Concurrency: one thread per candidate file (keep-alive session).
• Outputs a dense CSV; missing demand values remain blank.
"""

import os
import yaml
import requests
import pandas as pd
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openpyxl import load_workbook
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# ───────────── Tune here ─────────────────────────────────────────────────── #
BASE_URL        = "https://ost.al/wp-content/uploads"
SUFFIXES        = ["", "-1", "-2", "-3", "-4", "-001", "-002", "-003"]
FOLDERS         = (0, 1)       # month folder offsets: current & next
HTTP_TIMEOUT    = 3            # seconds per request
DEFAULT_WORKERS = 32           # used if MAX_WORKERS missing in config.yaml
VERBOSE         = False        # True = debug prints, bar hidden
# ─────────────────────────────────────────────────────────────────────────── #


def _find_sheet(wb):
    for name in wb.sheetnames:
        if name.strip().lower().startswith("publikime al"):
            return wb[name]
    raise KeyError("'Publikime AL' sheet not found")


def _date_from_c158(xlsx: bytes):
    try:
        wb = load_workbook(BytesIO(xlsx), read_only=True, data_only=True)
        value = _find_sheet(wb)["C158"].value
        if isinstance(value, str):
            return datetime.strptime(value.strip(), "%d.%m.%Y").date()
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, (int, float)):  # Excel serial
            return datetime.fromordinal(datetime(1899, 12, 30).toordinal() + int(value)).date()
    except Exception:
        pass
    return None


def _hourly_rows(xlsx: bytes, rep_date):
    wb = load_workbook(BytesIO(xlsx), read_only=True, data_only=True)
    vals = [_find_sheet(wb)[f"F{row}"].value for row in range(160, 184)]
    return [
        {"date": rep_date.isoformat(), "hour": h + 1, "demand": v}
        for h, v in enumerate(vals) if v is not None
    ]


# ─────────────────────────────────────────────────────────────────────────── #
def run(overwrite=False):
    # 1. read config --------------------------------------------------------- #
    cfg_file = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(cfg_file, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    start = datetime.strptime(cfg["START_DATE"], "%Y-%m-%d")
    end   = datetime.strptime(cfg["END_DATE"],   "%Y-%m-%d")
    out_dir = cfg["OUTPUT_DIR"]
    max_workers = int(cfg.get("MAX_WORKERS", DEFAULT_WORKERS))
    os.makedirs(out_dir, exist_ok=True)

    wanted_days = pd.date_range(start, end).date
    search_days = pd.date_range(start, end + relativedelta(months=1)).date

    # 2. worker (one *candidate date* per thread) ---------------------------- #
    def fetch(day):
        sess = requests.Session()  # keep-alive inside the thread
        for suf in SUFFIXES:
            for off in FOLDERS:
                folder = datetime(day.year, day.month, 1) + relativedelta(months=off)
                url = (
                    f"{BASE_URL}/{folder.year}/{folder.month:02d}/"
                    f"Publikimi-te-dhenave-{day.day:02d}.{day.month:02d}.{day.year}{suf}.xlsx"
                )
                try:
                    r = sess.get(url, timeout=HTTP_TIMEOUT)
                    if r.status_code != 200:
                        continue
                    rep = _date_from_c158(r.content)
                    if not rep or not (start.date() <= rep <= end.date()):
                        continue          # outside desired window
                    rows = _hourly_rows(r.content, rep)
                    if rows:
                        return rep, rows  # success – stop searching
                except Exception as exc:
                    if VERBOSE:
                        print("⚠", url, exc)
        return None                     # nothing useful for this *filename*

    # 3. concurrent execution ----------------------------------------------- #
    bar = tqdm(total=len(search_days), desc="OST", unit="file",
               dynamic_ncols=True, disable=VERBOSE)

    collected = {}   # rep_date → rows (keep longest if duplicates)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for fut in as_completed(pool.submit(fetch, d) for d in search_days):
            bar.update(1)
            res = fut.result()
            if res:
                rep, rows = res
                if rep not in collected or len(rows) > len(collected[rep]):
                    collected[rep] = rows
    bar.close()

    # 4. build full (date, hour) skeleton ------------------------------------ #
    skeleton = pd.MultiIndex.from_product(
        [pd.Series(wanted_days).astype(str), range(1, 25)],
        names=["date", "hour"]
    ).to_frame(index=False)

    real_rows = pd.DataFrame(
        [r for lst in collected.values() for r in lst],
        columns=["date", "hour", "demand"]
    )

    df = (
        skeleton
        .merge(real_rows, how="left", on=["date", "hour"])
        .sort_values(["date", "hour"])
    )

    # 5. save CSV ------------------------------------------------------------ #
    csv_path = os.path.join(out_dir, "ost_data.csv")
    df.to_csv(csv_path, index=False, na_rep="")
    print(f"✅ Saved {len(df):,} rows ({df['date'].nunique()} day(s)) → {csv_path}")

    missing = sorted(set(wanted_days) - set(pd.to_datetime(real_rows["date"]).dt.date))
    if missing:
        print(
            "\n⚠ No workbook found for:",
            ", ".join(d.isoformat() for d in missing),
            "\n   (looked one month ahead)",
        )


# ─────────────────────────────────────────────────────────────────────────── #
if __name__ == "__main__":
    run()
