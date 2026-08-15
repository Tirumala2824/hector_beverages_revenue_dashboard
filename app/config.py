from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime configuration with safe, explicit defaults for local development."""

    base_dir: Path
    data_path: Path
    template_dir: Path
    static_dir: Path
    host: str = "127.0.0.1"
    port: int = 8000

    @classmethod
    def from_environment(cls, base_dir: Path | None = None) -> Settings:
        root = (base_dir or Path(__file__).resolve().parents[1]).resolve()
        configured_data = Path(
            os.getenv("DASHBOARD_DATA_PATH", "data/Sales Data For Data Analyst Role (1).csv")
        )
        data_path = configured_data if configured_data.is_absolute() else root / configured_data
        return cls(
            base_dir=root,
            data_path=data_path,
            template_dir=root / "templates",
            static_dir=root / "static",
            host=os.getenv("DASHBOARD_HOST", "127.0.0.1"),
            port=int(os.getenv("DASHBOARD_PORT", "8000")),
        )
