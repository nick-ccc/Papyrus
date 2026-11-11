"""LaTeX template lookup. Templates are `<templates_dir>/<id>.tex`."""
from pathlib import Path

from .config import settings


class Template:
    def __init__(self, template_id: str, template_path: Path) -> None:
        self.id = template_id
        self.template_path = template_path

    def read(self) -> str:
        return self.template_path.read_text(encoding="utf-8")


class TemplateRegistry:

    def __init__(self, directory: Path) -> None:
        self.directory = directory.expanduser().resolve()

    def _scan(self) -> dict[str, Template]:
        if not self.directory.is_dir():
            return {}

        return {
            path.stem: Template(path.stem, path)
            for path in sorted(self.directory.glob("*.tex"))
            if path.is_file()
        }

    def ids(self) -> list[str]:
        return list(self._scan())

    def get(self, template_id: str) -> Template | None:
        return self._scan().get(template_id)


template_registry = TemplateRegistry(settings.templates_dir)
