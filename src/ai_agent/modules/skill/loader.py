"""Skill loader: reads YAML-frontmatter skill files, lazy-loads full content."""
from __future__ import annotations

import re
from functools import lru_cache
from typing import NamedTuple

from ai_agent.config.settings import BASE_DIR

SKILLS_DIR = BASE_DIR / "skills"

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_FIELD_RE = re.compile(r"^(\w+):\s*(.+)$", re.MULTILINE)


class SkillMeta(NamedTuple):
    name: str
    description: str


def _parse_frontmatter(text: str) -> dict[str, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    return dict(_FIELD_RE.findall(m.group(1)))


def list_skill_metas() -> list[SkillMeta]:
    """Read only frontmatter — fast startup, no full-content load."""
    if not SKILLS_DIR.exists():
        return []
    metas = []
    for path in sorted(SKILLS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        name = fm.get("name", path.stem)
        desc = fm.get("description", "")
        metas.append(SkillMeta(name=name, description=desc))
    return metas


@lru_cache(maxsize=None)
def load_skill(name: str) -> str:
    """Load full skill content by name. Cached after first read."""
    if not SKILLS_DIR.exists():
        return ""
    for path in sorted(SKILLS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        if fm.get("name", path.stem) == name:
            return _FRONTMATTER_RE.sub("", text).strip()
    return ""


def get_skills_summary() -> str:
    """Brief skill registry for system prompt — names and descriptions only."""
    metas = list_skill_metas()
    if not metas:
        return ""
    lines = ["## Available Skills"] + [
        f"- **{m.name}**: {m.description} — 调用 get_skill_guide('{m.name}') 获取完整指南"
        for m in metas
    ]
    return "\n".join(lines)
