from pathlib import Path

from .utils import now_iso


def append_log_line(log_path: Path, action: str, chemical_name: str, cas: str | None, details: str, user: str) -> None:
    line = f"{now_iso()} | {action} | {chemical_name} | CAS {cas or '-'} | user: {user} | details: {details}\n"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line)
