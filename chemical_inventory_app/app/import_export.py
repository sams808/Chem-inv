import csv
import shutil
from pathlib import Path

import pandas as pd

from .cas_tools import normalize_cas
from .models import ALLOWED_STATUSES

EXPECTED_COLUMNS = [
    "name", "cas", "formula", "supplier", "quantity", "unit", "physical_state",
    "location_room", "location_cabinet", "location_shelf", "location_detail",
    "hazard_text", "ghs_codes", "notes", "sds_local_path", "sds_url",
    "sds_status", "status",
]

# Accept both the app-native CSV headers and the cleaned inventory CSV headers
# produced from the original Excel inventory.
COLUMN_ALIASES = {
    "name": ["name", "material_name", "chemical_name", "product_name"],
    "cas": ["cas", "cas_number", "cas_raw", "cas_no", "casrn"],
    "formula": ["formula", "chemical_formula"],
    "supplier": ["supplier", "manufacturer", "vendor"],
    "quantity": ["quantity", "primary_quantity"],
    "unit": ["unit", "primary_unit"],
    "physical_state": ["physical_state", "state"],
    "location_room": ["location_room", "room", "location"],
    "location_cabinet": ["location_cabinet", "cabinet"],
    "location_shelf": ["location_shelf", "shelf"],
    "location_detail": ["location_detail", "location_notes", "location_detail_raw"],
    "hazard_text": ["hazard_text", "hazards_raw", "hazards"],
    "ghs_codes": ["ghs_codes", "ghs"],
    "notes": ["notes"],
    "sds_local_path": ["sds_local_path", "sds_path"],
    "sds_url": ["sds_url", "sds_link"],
    "sds_status": ["sds_status"],
    "status": ["status"],
}


def _norm_header(value: str) -> str:
    return str(value).strip().replace("\ufeff", "").lower()


def _clean(value) -> str | None:
    value = "" if value is None else str(value).strip()
    if not value or value.lower() in {"nan", "none", "null"}:
        return None
    return value


def _pick(row, *names: str) -> str | None:
    for name in names:
        value = _clean(row.get(_norm_header(name)))
        if value is not None:
            return value
    return None


def _status_from_row(row) -> str:
    status = _pick(row, "status")
    if status in ALLOWED_STATUSES:
        return status

    active = _pick(row, "active")
    if active is not None:
        if active.lower() in {"true", "1", "yes", "y", "active"}:
            return "active"
        if active.lower() in {"false", "0", "no", "n", "inactive", "archived"}:
            return "archived"

    return "active"


def _normalize_ghs(value: str | None) -> str | None:
    if value is None:
        return None
    # The UI parser accepts semicolon-separated or comma-separated codes.
    # Store semicolons for readability and to avoid ambiguity with CSV commas.
    codes = [x.strip().upper() for x in value.replace(",", ";").split(";") if x.strip()]
    return ";".join(codes) if codes else None


def _combine_notes(row, base_notes: str | None) -> str | None:
    parts = []
    if base_notes:
        parts.append(base_notes)

    for key, label in [
        ("family", "family"),
        ("hazard_tags", "hazard_tags"),
        ("hazard_rank_0_5", "hazard_rank_0_5"),
        ("quantity_gas_ft3", "quantity_gas_ft3"),
        ("quantity_liquid_l", "quantity_liquid_l"),
        ("quantity_solid_kg", "quantity_solid_kg"),
    ]:
        value = _pick(row, key)
        if value is not None:
            parts.append(f"{label}: {value}")

    return " | ".join(parts) if parts else None


def _quantity_to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def _row_to_record(row) -> dict:
    rec = {}

    for col in EXPECTED_COLUMNS:
        aliases = COLUMN_ALIASES.get(col, [col])
        rec[col] = _pick(row, *aliases)

    rec["status"] = _status_from_row(row)
    rec["ghs_codes"] = _normalize_ghs(rec.get("ghs_codes"))
    rec["notes"] = _combine_notes(row, rec.get("notes"))

    if rec.get("cas"):
        rec["cas"] = normalize_cas(rec["cas"])

    rec["quantity"] = _quantity_to_float(rec.get("quantity"))

    if not rec.get("sds_status"):
        rec["sds_status"] = "unknown"

    # Remove empty values but keep explicit fields that are useful in exports.
    return {k: v for k, v in rec.items() if v is not None}


def import_csv(db, csv_path: Path) -> int:
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False).fillna("")
    df.columns = [_norm_header(c) for c in df.columns]

    count = 0

    for _, row in df.iterrows():
        rec = _row_to_record(row)

        # Empty category/header rows from the original Excel sheet are not products.
        if not rec.get("name"):
            continue

        cid = db.add_chemical(rec)
        db.log_action("IMPORT", cid, rec.get("name", ""), rec.get("cas"), "csv import")
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
