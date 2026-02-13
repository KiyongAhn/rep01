"""Skill Registry: manages skill metadata discovery and search."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SkillMeta:
    """Parsed metadata from a skill's skill.yaml."""

    name: str
    description: str
    triggers: list[str]
    entry_point: str
    version: str = "1.0.0"
    directory: Path = field(default_factory=lambda: Path("."))


class SkillRegistry:
    """Discovers and indexes skills from the filesystem.

    Parameters
    ----------
    base_path:
        Root directory that contains individual skill sub-directories.
        Defaults to the ``SKILLS_BASE_PATH`` env-var, or ``./skills``.
    """

    def __init__(self, base_path: Optional[str] = None) -> None:
        resolved = base_path or os.environ.get("SKILLS_BASE_PATH", "./skills")
        self.base_path = Path(resolved).resolve()
        self._skills: dict[str, SkillMeta] = {}
        self._load_skills()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_skills(self, query: str, context: str = "") -> list[dict]:
        """Return skills whose trigger keywords match *query* or *context*.

        The matching is intentionally simple: every trigger phrase is checked
        against the lowered query + context string.  This keeps the registry
        deterministic and fast (no LLM call needed).
        """
        combined = f"{query} {context}".lower()
        results: list[dict] = []
        for skill in self._skills.values():
            for trigger in skill.triggers:
                if trigger.lower() in combined:
                    results.append(self._skill_to_dict(skill))
                    break
        return results

    def get_skill_by_name(self, name: str) -> Optional[SkillMeta]:
        return self._skills.get(name)

    def list_skills(self) -> list[dict]:
        return [self._skill_to_dict(s) for s in self._skills.values()]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_skills(self) -> None:
        """Scan *base_path* for sub-directories containing ``skill.yaml``."""
        if not self.base_path.is_dir():
            logger.warning("Skills base path does not exist: %s", self.base_path)
            return

        for child in sorted(self.base_path.iterdir()):
            if not child.is_dir():
                continue
            yaml_path = child / "skill.yaml"
            if not yaml_path.exists():
                continue
            try:
                meta = self._parse_yaml(yaml_path, child)
                self._skills[meta.name] = meta
                logger.info("Loaded skill: %s (v%s)", meta.name, meta.version)
            except Exception:
                logger.exception("Failed to load skill from %s", child)

    @staticmethod
    def _parse_yaml(yaml_path: Path, directory: Path) -> SkillMeta:
        with open(yaml_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)

        return SkillMeta(
            name=data["name"],
            description=data["description"],
            triggers=data.get("triggers", []),
            entry_point=data.get("entry_point", "main.py"),
            version=str(data.get("version", "1.0.0")),
            directory=directory,
        )

    @staticmethod
    def _skill_to_dict(skill: SkillMeta) -> dict:
        return {
            "name": skill.name,
            "description": skill.description,
            "triggers": skill.triggers,
            "version": skill.version,
        }
