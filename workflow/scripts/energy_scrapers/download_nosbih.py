# energy_scrapers/download_nosbih.py
import os
import yaml
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup


def _col_index(header_cells, th_id: str) -> int | None:
    """Return the index of <th id=th_id> in header_cells or None."""
    for i, th in enumerate(header_cells):
        if th.get("id") == th_id:
            return i
    return None


def _replace_flat_stretches(actual: list[float | None],
                            planned: list[float | None]) -> list[float | None]:
    """
    If the same *actual* demand repeats 3+ hours in a row, swap that whole
    streak with *planned* (when available).  Also used later for None / 0.
    """
    final = actual[:]
    i = 0
    while i < 24:
        val = actual[i]
        streak_start = i
        while i + 1 < 24 and actual[i + 1] == val and val not in (None, 0):
            i += 1
        streak_len = i - streak_start + 1
        if streak_len >= 3:
            for j in range(streak_start, streak_start + streak_len):
                if planned[j] not in (None, 0):
                    final[j] = planned[j]
        i += 1
    return final


def run(overwrite: bool = False) -> None:
    # ------------------------------------------------------------------ #
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(cfg_path, encoding="utf-8") as fp:
        cfg = yaml.safe_load(fp)

    START   = datetime.strptime(cfg["START_DATE"], "%Y-%m-%d")
    END     = datetime.strptime(cfg["END_DATE"], "%Y-%m-%d")
    OUTDIR  = cfg["OUTPUT_DIR"]
    os.makedirs(OUTDIR, exist_ok=True)

    url     = "https://www.nosbih.ba/en/wp-admin/admin-ajax.php"
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}

    all_rows: list[dict] = []
    for day in tqdm([START + timedelta(d) for d in range((END - START).days + 1)],
                    desc="NOSBiH", unit="day"):

        if day.month == 2 and day.day == 29:   # site has no leap-day data
            continue

        date_str     = day.strftime("%d.%m.%Y.")
        display_date = day.strftime("%Y-%m-%d")
        try:
            resp = requests.post(
                url,
                data={"action": "production", "production": f"date={date_str}"},
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
        except Exception as exc:
            print(f"⚠️  {display_date}: fetch failed – {exc}")
            continue

        html = resp.json().get("data", "")
        soup = BeautifulSoup(html, "html.parser")
        header_cells = soup.select("table#productionTable thead tr th")
        body_rows    = soup.select("table#productionTable tbody tr")
        if not header_cells or not body_rows:
            print(f"⚠️  {display_date}: malformed table")
            continue

        # map column indices
        idx_actual  = _col_index(header_cells, "label-consumption-actual")
        idx_planned = _col_index(header_cells, "label-consumption-planned")
        idx_gen     = _col_index(header_cells, "label-production-hydropower") or 2
        if idx_actual is None or idx_planned is None:
            print(f"⚠️  {display_date}: header IDs not found")
            continue

        # pre-allocate 24-slot holders
        actual_vals  = [None] * 24
        planned_vals = [None] * 24
        gen_vals     = [None] * 24

        for r in body_rows:
            cols = r.find_all("td")
            if len(cols) <= max(idx_actual, idx_planned, idx_gen):
                continue
            hour_txt = cols[0].text.strip()      # e.g. '01:00'
            try:
                hour_idx = int(hour_txt.split(":")[0]) - 1  # 0-based
            except ValueError:
                continue

            def _num(cell):
                txt = cell.text.strip().replace(",", ".")
                return float(txt) if txt else None

            gen_vals[hour_idx]     = _num(cols[idx_gen])
            actual_vals[hour_idx]  = _num(cols[idx_actual])
            planned_vals[hour_idx] = _num(cols[idx_planned])

        # 1) replace None / 0 with planned
        final_demand = [
            p if (a in (None, 0)) and (p not in (None, 0)) else a
            for a, p in zip(actual_vals, planned_vals)
        ]
        # 2) replace flat stretches
        final_demand = _replace_flat_stretches(final_demand, planned_vals)

        # append to the master list
        for h in range(24):
            all_rows.append(
                {
                    "date": display_date,
                    "hour": h + 1,
                    "power_generation": gen_vals[h],
                    "demand": final_demand[h],
                }
            )

    df = pd.DataFrame(all_rows)
    out_csv = os.path.join(OUTDIR, "nosbih_data.csv")
    df.to_csv(out_csv, index=False, na_rep="")
    print(f"✅ NOSBiH data saved to {out_csv} "
          f"({df['date'].nunique()} days, {df['demand'].count()} hourly demand values)")
