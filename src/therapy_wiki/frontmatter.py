"""Simple Markdown frontmatter rendering without third-party YAML."""

from pathlib import Path
from typing import Any, Dict, Iterable


def _render_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace('"', '\\"')
    return f'"{escaped}"'


def _render_list(values: Iterable[Any], indent: int = 0) -> str:
    pad = " " * indent
    lines = []
    for value in values:
        if isinstance(value, dict):
            lines.append(f"{pad}-")
            lines.append(_render_mapping(value, indent + 2))
        else:
            lines.append(f"{pad}- {_render_scalar(value)}")
    return "\n".join(lines)


def _render_mapping(payload: Dict[str, Any], indent: int = 0) -> str:
    pad = " " * indent
    lines = []
    for key, value in payload.items():
        if isinstance(value, dict):
            lines.append(f"{pad}{key}:")
            lines.append(_render_mapping(value, indent + 2))
        elif isinstance(value, list):
            lines.append(f"{pad}{key}:")
            lines.append(_render_list(value, indent + 2))
        else:
            lines.append(f"{pad}{key}: {_render_scalar(value)}")
    return "\n".join(lines)


def render_markdown(frontmatter: Dict[str, Any], body: str) -> str:
    return "---\n{}\n---\n\n{}".format(_render_mapping(frontmatter), body.strip() + "\n")


def write_markdown(path: Path, frontmatter: Dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(frontmatter, body), encoding="utf-8")

