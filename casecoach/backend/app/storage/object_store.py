from __future__ import annotations

import json
from pathlib import Path
from typing import Any, BinaryIO


class ObjectStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def job_dir(self, job_id: str) -> Path:
        path = self.root / "jobs" / job_id
        path.mkdir(parents=True, exist_ok=True)
        for name in ("uploads", "preprocessed", "frames", "slides", "artifacts"):
            (path / name).mkdir(parents=True, exist_ok=True)
        return path

    def relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def resolve(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path

    def write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def read_json(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def copy_stream_limited(self, source: BinaryIO, destination: Path, max_bytes: int) -> int:
        destination.parent.mkdir(parents=True, exist_ok=True)
        total = 0
        with destination.open("wb") as target:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(f"Upload exceeds max size of {max_bytes} bytes.")
                target.write(chunk)
        return total

