"""Hàng đợi cục bộ (SQLite): job, ACK chờ gửi (outbox), ảnh chờ upload. Sống sót qua mất điện/mất mạng."""
import json
import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY, payload TEXT NOT NULL, state TEXT NOT NULL, play_at REAL NOT NULL,
  audio_path TEXT, attempts INTEGER DEFAULT 0, next_try REAL DEFAULT 0, error TEXT,
  before_done INTEGER DEFAULT 0, start_done INTEGER DEFAULT 0, after_due REAL, after_done INTEGER DEFAULT 0,
  updated REAL
);
CREATE TABLE IF NOT EXISTS outbox (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS uploads (
  id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT, phase TEXT, path TEXT, captured_at TEXT,
  attempts INTEGER DEFAULT 0, next_try REAL DEFAULT 0
);
"""


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.lock = threading.RLock()

    def q(self, sql, args=()):
        with self.lock:
            return self.db.execute(sql, args).fetchall()

    def x(self, sql, args=()):
        with self.lock:
            return self.db.execute(sql, args)

    # jobs
    def get_job(self, job_id):
        rows = self.q("SELECT * FROM jobs WHERE job_id=?", (job_id,))
        return dict(rows[0]) if rows else None

    def add_job(self, payload: dict, play_at: float, now: float):
        self.x("INSERT INTO jobs(job_id,payload,state,play_at,updated) VALUES(?,?,?,?,?)",
               (payload["job_id"], json.dumps(payload), "received", play_at, now))

    def update_job(self, job_id, now: float, **fields):
        fields["updated"] = now
        cols = ",".join(f"{k}=?" for k in fields)
        self.x(f"UPDATE jobs SET {cols} WHERE job_id=?", (*fields.values(), job_id))

    def jobs_in(self, *states):
        marks = ",".join("?" * len(states))
        return [dict(r) for r in self.q(f"SELECT * FROM jobs WHERE state IN ({marks}) ORDER BY play_at", states)]

    def all_jobs(self):
        return [dict(r) for r in self.q("SELECT * FROM jobs ORDER BY play_at")]

    # outbox (ACK)
    def push_ack(self, payload: dict):
        self.x("INSERT INTO outbox(payload) VALUES(?)", (json.dumps(payload),))

    def pending_acks(self):
        return [(r["id"], json.loads(r["payload"])) for r in self.q("SELECT * FROM outbox ORDER BY id")]

    def drop_ack(self, ack_id):
        self.x("DELETE FROM outbox WHERE id=?", (ack_id,))

    # uploads
    def push_upload(self, job_id, phase, path, captured_at):
        self.x("INSERT INTO uploads(job_id,phase,path,captured_at) VALUES(?,?,?,?)", (job_id, phase, str(path), captured_at))

    def due_uploads(self, now: float):
        return [dict(r) for r in self.q("SELECT * FROM uploads WHERE next_try<=? ORDER BY id", (now,))]

    def retry_upload(self, up_id, attempts, next_try):
        self.x("UPDATE uploads SET attempts=?, next_try=? WHERE id=?", (attempts, next_try, up_id))

    def drop_upload(self, up_id):
        self.x("DELETE FROM uploads WHERE id=?", (up_id,))
