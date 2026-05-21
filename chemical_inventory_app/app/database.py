import sqlite3
from pathlib import Path

from .logging_tools import append_log_line
from .models import ALLOWED_STATUSES
from .utils import now_iso


class DatabaseManager:
    def __init__(self, db_path: Path, base_dir: Path):
        self.db_path = db_path
        self.base_dir = base_dir
        self.log_path = base_dir / "data/logs/inventory_changes.log"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

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
              chemical_id INTEGER, chemical_name TEXT, cas TEXT, details TEXT, user TEXT);
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
            """)

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

    def list_chemicals(self):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM chemicals ORDER BY name COLLATE NOCASE").fetchall()

    def log_action(self, action: str, chemical_id: int | None, chemical_name: str, cas: str | None, details: str = "", user: str = "local_user"):
        ts = now_iso()
        with self.connect() as conn:
            conn.execute("INSERT INTO logs (timestamp, action, chemical_id, chemical_name, cas, details, user) VALUES (?,?,?,?,?,?,?)", (ts, action, chemical_id, chemical_name, cas, details, user))
        append_log_line(self.log_path, action, chemical_name, cas, details, user)
