from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    database_url: str
    qwen_vl_base_url: str
    qwen_vl_api_key: str
    qwen_vl_model: str
    qwen_omni_base_url: str
    qwen_omni_api_key: str
    qwen_omni_model: str
    tavily_api_key: str
    deepgram_api_key: str
    asr_provider: str
    asr_model: str
    max_upload_mb: int

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def sqlite_path(self) -> Path:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            raise ValueError("Only sqlite:/// DATABASE_URL values are supported in the MVP.")
        value = self.database_url[len(prefix) :]
        path = Path(value)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    _load_dotenv(Path.cwd() / ".env")
    data_dir = Path(os.getenv("CASECOACH_DATA_DIR", "./data"))
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{data_dir / 'casecoach.sqlite3'}")
    return Settings(
        data_dir=data_dir,
        database_url=database_url,
        qwen_vl_base_url=os.getenv("QWEN_VL_BASE_URL", ""),
        qwen_vl_api_key=os.getenv("QWEN_VL_API_KEY", ""),
        qwen_vl_model=os.getenv("QWEN_VL_MODEL", "qwen3.6-plus"),
        qwen_omni_base_url=os.getenv("QWEN_OMNI_BASE_URL", ""),
        qwen_omni_api_key=os.getenv("QWEN_OMNI_API_KEY", ""),
        qwen_omni_model=os.getenv("QWEN_OMNI_MODEL", "Qwen/Qwen3-Omni-30B-A3B-Thinking"),
        tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
        deepgram_api_key=os.getenv("DEEPGRAM_API_KEY", ""),
        asr_provider=os.getenv("ASR_PROVIDER", "faster_whisper"),
        asr_model=os.getenv("ASR_MODEL", "base"),
        max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "1024")),
    )


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
