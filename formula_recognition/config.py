import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MODEL = "glm-4.1v-thinking-flashx"
DEFAULT_ENDPOINT = ""


@dataclass(eq=True)
class AppConfig:
    api_key: str = ""
    endpoint: str = DEFAULT_ENDPOINT
    model: str = DEFAULT_MODEL
    hotkey: str = "ctrl+alt+m"
    history_dir: str = ""
    auto_copy: bool = True
    save_screenshot: bool = True
    close_to_tray: bool = True


class AppConfigStore:
    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)

    def load(self) -> AppConfig:
        if not self.config_path.exists():
            default = AppConfig(history_dir=str(self.config_path.parent / "history"))
            self.save(default)
            return default

        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        glm = data.get("glm", {}) if isinstance(data.get("glm", {}), dict) else {}
        history_dir = data.get("history_dir", str(self.config_path.parent / "history"))

        return AppConfig(
            api_key=glm.get("api_key", data.get("api_key", "")),
            endpoint=glm.get("endpoint", data.get("endpoint", DEFAULT_ENDPOINT)),
            model=glm.get("model", data.get("model", DEFAULT_MODEL)),
            hotkey=data.get("hotkey", "ctrl+alt+m"),
            history_dir=history_dir,
            auto_copy=data.get("auto_copy", True),
            save_screenshot=data.get("save_screenshot", True),
            close_to_tray=data.get("close_to_tray", True),
        )

    def save(self, config: AppConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "glm": {
                "api_key": config.api_key,
                "endpoint": config.endpoint,
                "model": config.model,
            },
            "hotkey": config.hotkey,
            "history_dir": config.history_dir,
            "auto_copy": config.auto_copy,
            "save_screenshot": config.save_screenshot,
            "close_to_tray": config.close_to_tray,
        }
        self.config_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
