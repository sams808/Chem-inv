from pathlib import Path

from .utils import now_iso


def append_log_line(log_path: Path, action: str, chemical_name: str, cas: str | None, details: str, user: str, mode: str = "Regular") -> None:
    line = f"{now_iso()} | {mode} | {action} | {chemical_name} | CAS {cas or '-'} | user: {user} | details: {details}\n"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line)
