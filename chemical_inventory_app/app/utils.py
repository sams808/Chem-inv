from datetime import datetime
from pathlib import Path


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_app_directories(base_dir: Path) -> None:
    for rel in ["data", "data/logs", "data/sds", "data/ghs_pictograms", "data/exports"]:
        (base_dir / rel).mkdir(parents=True, exist_ok=True)
    (base_dir / "data/logs/inventory_changes.log").touch(exist_ok=True)
