import hashlib
import sqlite3
from pathlib import Path

from .logging_tools import append_log_line
from .models import ALLOWED_STATUSES
from .utils import now_iso


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


class DatabaseManager:
    def __init__(self, db_path: Path, base_dir: Path):
        self.db_path = db_path
        self.base_dir = base_dir
        self.log_path = base_dir / "data/logs/inventory_changes.log"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_column(self, conn, table: str, column: str, definition: str):
        cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def initialize(self):
        with self.connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS chemicals (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL, cas TEXT, formula TEXT, supplier TEXT, quantity REAL,
              unit TEXT, physical_state TEXT, location_room TEXT, location_cabinet TEXT,
              location_shelf TEXT, location_detail TEXT, hazard_text TEXT, ghs_codes TEXT,
              notes TEXT, sds_local_path TEXT, sds_url TEXT, sds_status TEXT DEFAULT 'unknown',
              status TEXT DEFAULT 'active', date_added TEXT, date_modified TEXT);
            CREATE TABLE IF NOT EXISTS logs (
              id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, action TEXT NOT NULL,
              chemical_id INTEGER, chemical_name TEXT, cas TEXT, details TEXT, user TEXT, mode TEXT);
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
            """)
            self._ensure_column(conn, "chemicals", "location_code", "TEXT")
            self._ensure_column(conn, "logs", "mode", "TEXT")
            conn.execute(
                """
                UPDATE chemicals
                SET location_code = TRIM(
                    COALESCE(NULLIF(location_room, ''), '') ||
                    CASE WHEN NULLIF(location_cabinet, '') IS NOT NULL THEN ' ' || location_cabinet ELSE '' END ||
                    CASE WHEN NULLIF(location_shelf, '') IS NOT NULL THEN ' ' || location_shelf ELSE '' END ||
                    CASE WHEN NULLIF(location_detail, '') IS NOT NULL THEN ' ' || location_detail ELSE '' END
                )
                WHERE (location_code IS NULL OR TRIM(location_code)='')
                """
            )
            row = conn.execute("SELECT value FROM settings WHERE key=?", ("admin_pin_hash",)).fetchone()
            if row is None:
                # TODO: replace with hashed password / lab-specific setting before real deployment.
                conn.execute("INSERT INTO settings(key, value) VALUES(?, ?)", ("admin_pin_hash", _hash_pin("1234")))

    def get_setting(self, key: str, default=None):
        with self.connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self.connect() as conn:
            conn.execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    def verify_admin_pin(self, pin: str) -> bool:
        return _hash_pin(pin) == self.get_setting("admin_pin_hash", "")

    def add_chemical(self, data: dict) -> int:
        now = now_iso()
        data.setdefault("status", "active")
        if data["status"] not in ALLOWED_STATUSES:
            data["status"] = "active"
        data["date_added"] = now
        data["date_modified"] = now
        cols = ",".join(data.keys())
        q = ",".join("?" for _ in data)
        with self.connect() as conn:
            cur = conn.execute(f"INSERT INTO chemicals ({cols}) VALUES ({q})", tuple(data.values()))
            return cur.lastrowid

    def update_chemical(self, chemical_id: int, data: dict):
        data["date_modified"] = now_iso()
        sets = ",".join(f"{k}=?" for k in data)
        with self.connect() as conn:
            conn.execute(f"UPDATE chemicals SET {sets} WHERE id=?", tuple(data.values()) + (chemical_id,))


    def delete_chemical(self, chemical_id: int):
        with self.connect() as conn:
            conn.execute("DELETE FROM chemicals WHERE id=?", (chemical_id,))

    def clear_inventory(self, mode: str = "Regular"):
        with self.connect() as conn:
            conn.execute("DELETE FROM chemicals")
            conn.execute("DELETE FROM sqlite_sequence WHERE name='chemicals'")
        self.log_action("CLEAR_INVENTORY", None, "inventory", None, "cleared all chemicals", mode=mode)

    def list_chemicals(self):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM chemicals ORDER BY name COLLATE NOCASE").fetchall()

    def list_logs(self):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()

    def log_action(self, action: str, chemical_id: int | None, chemical_name: str, cas: str | None, details: str = "", user: str = "local_user", mode: str = "Regular"):
        ts = now_iso()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO logs (timestamp, action, chemical_id, chemical_name, cas, details, user, mode) VALUES (?,?,?,?,?,?,?,?)",
                (ts, action, chemical_id, chemical_name, cas, details, user, mode),
            )
        append_log_line(self.log_path, action, chemical_name, cas, details, user, mode)
