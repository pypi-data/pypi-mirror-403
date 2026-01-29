"""Shared helpers for Planar CLI documentation metadata."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

__all__ = [
    "DocCommand",
    "DOC_COMMANDS",
    "README_PATH",
    "DOCS_DIR",
    "read_markdown",
    "render_docs_index",
]


@dataclass(frozen=True)
class DocCommand:
    """Represents a documentation snippet exposed through the CLI."""

    name: str
    path: Path
    description: str


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
README_PATH = REPO_ROOT / "README.md"

DOC_COMMANDS: tuple[DocCommand, ...] = (
    DocCommand(
        "all",
        DOCS_DIR / "llm_prompt.md",
        "Complete LLM prompt reference.",
    ),
    DocCommand(
        "workflows",
        DOCS_DIR / "workflows.md",
        "Durable workflows guide.",
    ),
    DocCommand(
        "agents",
        DOCS_DIR / "agents.md",
        "Agent capabilities overview.",
    ),
    DocCommand(
        "entities",
        DOCS_DIR / "entities.md",
        "Entity helpers and patterns.",
    ),
    DocCommand(
        "testing",
        DOCS_DIR / "testing_workflows.md",
        "Workflow testing guide.",
    ),
    DocCommand(
        "sqlalchemy",
        DOCS_DIR / "sqlalchemy_usage.md",
        "SQLAlchemy integration tips.",
    ),
    DocCommand(
        "planar-dataset",
        DOCS_DIR / "planar_dataset.md",
        "Planar dataset reference.",
    ),
)


def read_markdown(path: Path) -> str:
    """Return the UTF-8 contents of a markdown file."""
    return path.read_text(encoding="utf-8")


def _docs_index_lines(commands: Iterable[DocCommand]) -> list[str]:
    lines = ["available documentation commands:"]
    for command in commands:
        lines.append(f"- {command.name:17} {command.description}")
    return lines


def render_docs_index() -> str:
    """Render the default ``planar docs`` output."""
    lines = _docs_index_lines(DOC_COMMANDS)
    lines.append("")
    try:
        lines.append(read_markdown(README_PATH))
    except OSError as exc:
        lines.append(f"README not available: {exc}")
    lines.append("")
    lines.append(
        "Tip: run `uv run planar docs <section>` to view any document in full."
    )
    return "\n".join(lines)
