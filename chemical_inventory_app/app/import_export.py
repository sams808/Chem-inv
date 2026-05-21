import csv
import shutil
from pathlib import Path

import pandas as pd

from .cas_tools import normalize_cas
from .models import ALLOWED_STATUSES

EXPECTED_COLUMNS = ["name","cas","formula","supplier","quantity","unit","physical_state","location_room","location_cabinet","location_shelf","location_detail","hazard_text","ghs_codes","notes","sds_local_path","sds_url","sds_status","status"]


def import_csv(db, csv_path: Path) -> int:
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    count = 0
    for _, row in df.iterrows():
        rec = {}
        for col in EXPECTED_COLUMNS:
            if col in row.index:
                v = row[col].strip()
                rec[col] = v if v else None
        if not rec.get("name"):
            continue
        if rec.get("cas"):
            rec["cas"] = normalize_cas(rec["cas"])
        if rec.get("quantity"):
            try:
                rec["quantity"] = float(rec["quantity"])
            except ValueError:
                rec["quantity"] = None
        if rec.get("status") not in ALLOWED_STATUSES:
            rec["status"] = "active"
        cid = db.add_chemical(rec)
        db.log_action("IMPORT", cid, rec.get("name", ""), rec.get("cas"), "initial import")
        count += 1
    return count


def export_rows(rows, path: Path):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows([dict(r) for r in rows])


def backup_database(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"inventory_backup_{db_path.stat().st_mtime_ns}.db"
    shutil.copy2(db_path, target)
    return target
