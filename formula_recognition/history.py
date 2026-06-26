from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class HistoryRecord:
    timestamp: datetime
    latex: str
    confidence: Optional[float]
    status: str
    error: Optional[str] = None
    image_extension: str = "png"


@dataclass
class HistoryEntry:
    path: Path
    timestamp: str
    status: str
    image: str
    confidence: str
    error: str
    latex: str


class HistoryStore:
    def __init__(self, history_dir: Path):
        self.history_dir = Path(history_dir)

    def write(self, record: HistoryRecord, image_bytes: bytes, save_image: bool = True) -> Tuple[Optional[Path], Path]:
        day_dir = self.history_dir / record.timestamp.strftime("%Y-%m-%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        stem = record.timestamp.strftime("%Y%m%d-%H%M%S")

        image_path = day_dir / "{}.{}".format(stem, record.image_extension) if save_image else None
        markdown_path = day_dir / "{}.md".format(stem)

        if image_path is not None:
            image_path.write_bytes(image_bytes)

        image_name = image_path.name if image_path is not None else "not saved"
        markdown_path.write_text(self._render_markdown(record, image_name), encoding="utf-8")
        return image_path, markdown_path

    def _render_markdown(self, record: HistoryRecord, image_name: str) -> str:
        confidence = "" if record.confidence is None else "{:.2f}".format(record.confidence)
        return (
            "# Formula Recognition Record\n\n"
            "- Time: {}\n".format(record.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            + "- Status: {}\n".format(record.status)
            + "- Image: {}\n".format(image_name)
            + "- Confidence: {}\n".format(confidence)
            + "- Error: {}\n\n".format(record.error or "")
            + "## LaTeX\n"
            + "```latex\n"
            + "{}\n".format(record.latex)
            + "```\n"
        )

    def list_records(self):
        if not self.history_dir.exists():
            return []

        entries = []
        for path in self.history_dir.glob("*/*.md"):
            entries.append(self._read_entry(path))
        return sorted(entries, key=lambda entry: entry.timestamp, reverse=True)

    def _read_entry(self, path: Path) -> HistoryEntry:
        text = path.read_text(encoding="utf-8")
        fields = {}
        for line in text.splitlines():
            if line.startswith("- ") and ": " in line:
                key, value = line[2:].split(": ", 1)
                fields[key.strip().lower()] = value.strip()

        latex = ""
        marker = "```latex"
        if marker in text:
            tail = text.split(marker, 1)[1]
            latex = tail.split("```", 1)[0].strip()

        return HistoryEntry(
            path=path,
            timestamp=fields.get("time", ""),
            status=fields.get("status", ""),
            image=fields.get("image", ""),
            confidence=fields.get("confidence", ""),
            error=fields.get("error", ""),
            latex=latex,
        )
