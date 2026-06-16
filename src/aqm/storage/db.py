"""SQLite time-series storage.

Long-format schema (one row per metric per timestamp) keeps it trivial to add
new metrics without migrations. WAL mode lets the collector write while the web
app and display read concurrently from separate processes.
"""
from __future__ import annotations

import sqlite3
from typing import Dict, List, Tuple

_SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    ts     INTEGER NOT NULL,   -- epoch seconds
    metric TEXT    NOT NULL,
    value  REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_readings_metric_ts ON readings (metric, ts);
"""


class Database:
    def __init__(self, path: str):
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def insert_readings(self, ts: int, values: Dict[str, float]) -> None:
        rows = [(ts, k, float(v)) for k, v in values.items() if v is not None]
        if not rows:
            return
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO readings (ts, metric, value) VALUES (?, ?, ?)", rows
            )

    def latest(self) -> Dict[str, Tuple[float, int]]:
        """Most recent value per metric -> {metric: (value, ts)}."""
        query = """
            SELECT r.metric, r.value, r.ts
            FROM readings r
            JOIN (SELECT metric, MAX(ts) AS mts FROM readings GROUP BY metric) m
              ON r.metric = m.metric AND r.ts = m.mts
        """
        with self._connect() as conn:
            return {metric: (value, ts) for metric, value, ts in conn.execute(query)}

    def history(self, metric: str, since_ts: int) -> List[Tuple[int, float]]:
        query = "SELECT ts, value FROM readings WHERE metric = ? AND ts >= ? ORDER BY ts"
        with self._connect() as conn:
            return [(ts, value) for ts, value in conn.execute(query, (metric, since_ts))]

    def prune(self, older_than_ts: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM readings WHERE ts < ?", (older_than_ts,))
