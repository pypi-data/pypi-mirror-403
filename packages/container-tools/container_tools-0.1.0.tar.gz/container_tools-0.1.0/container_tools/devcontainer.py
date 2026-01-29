import json
from pathlib import Path


def strip_comments(text: str) -> str:
    lines = text.split('\n')
    non_comment_lines = [l for l in lines if not l.strip().startswith('//')]

    return "\n".join(non_comment_lines)


def parse_devcontainer(path: str | Path) -> dict:
    path = Path(path)
    raw = path.read_text(encoding="utf-8")

    cleaned = strip_comments(raw)

    return json.loads(cleaned)


class Devcontainer:
    DEFAULT_PATH = ".devcontainer/devcontainer.json"

    image: str = None
    mounts: list[str] = None
    containerEnv: dict[str, str] = None

    def __init__(self, path: str | Path | None = None):
        self._path = Path(path) if path else Path(self.DEFAULT_PATH)

    def parse(self):
        if not self._path.exists():
            raise FileNotFoundError(f"Devcontainer file not found: {self._path}")

        data = parse_devcontainer(self._path)

        for key, value in data.items():
            setattr(self, key, value)
