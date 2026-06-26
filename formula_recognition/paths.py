from pathlib import Path
from typing import Optional


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir(base_dir: Optional[Path] = None) -> Path:
    root = Path(base_dir) if base_dir else Path.cwd()
    return ensure_dir(root / "data")


def get_default_config_path(base_dir: Optional[Path] = None) -> Path:
    return get_data_dir(base_dir) / "config.json"


def get_default_history_dir(base_dir: Optional[Path] = None) -> Path:
    return ensure_dir(get_data_dir(base_dir) / "history")
