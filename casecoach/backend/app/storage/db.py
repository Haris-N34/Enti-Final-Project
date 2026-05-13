from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class JobStore:
    def __init__(self, sqlite_path: Path):
        self.sqlite_path = sqlite_path
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                  job_id TEXT PRIMARY KEY,
                  status TEXT NOT NULL,
                  error TEXT,
                  metadata_json TEXT NOT NULL,
                  paths_json TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )

    def create_job(self, job_id: str, metadata: dict[str, Any], paths: dict[str, str]) -> dict[str, Any]:
        now = utc_now()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (job_id, status, error, metadata_json, paths_json, created_at, updated_at)
                VALUES (?, ?, NULL, ?, ?, ?, ?)
                """,
                (job_id, "uploaded", json.dumps(metadata), json.dumps(paths), now, now),
            )
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._row_to_dict(row)

    def update_status(self, job_id: str, status: str, error: str | None = None) -> dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, error = ?, updated_at = ? WHERE job_id = ?",
                (status, error, utc_now(), job_id),
            )
        return self.get_job(job_id)

    def update_metadata(self, job_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
        job = self.get_job(job_id)
        merged = {**job["metadata"], **metadata}
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET metadata_json = ?, updated_at = ? WHERE job_id = ?",
                (json.dumps(merged), utc_now(), job_id),
            )
        return self.get_job(job_id)

    def update_paths(self, job_id: str, paths: dict[str, str]) -> dict[str, Any]:
        job = self.get_job(job_id)
        merged = {**job["paths"], **paths}
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET paths_json = ?, updated_at = ? WHERE job_id = ?",
                (json.dumps(merged), utc_now(), job_id),
            )
        return self.get_job(job_id)

    def fail_job(self, job_id: str, error: str) -> dict[str, Any]:
        return self.update_status(job_id, "failed", error)

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "job_id": row["job_id"],
            "status": row["status"],
            "error": row["error"],
            "metadata": json.loads(row["metadata_json"]),
            "paths": json.loads(row["paths_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

