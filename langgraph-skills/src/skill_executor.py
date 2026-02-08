"""Skill Executor: loads skill context and runs skill entry points."""

from __future__ import annotations

import importlib.util
import json
import logging
from pathlib import Path
from typing import Any, Optional

from .skill_registry import SkillMeta, SkillRegistry

logger = logging.getLogger(__name__)


class SkillExecutor:
    """Loads context files and dynamically executes skill entry points.

    Parameters
    ----------
    registry:
        A :class:`SkillRegistry` instance used to resolve skill names to
        their on-disk locations.
    """

    def __init__(self, registry: SkillRegistry) -> None:
        self.registry = registry

    # ------------------------------------------------------------------
    # Context loading
    # ------------------------------------------------------------------

    def load_skill_context(self, skill_name: str) -> dict[str, Any]:
        """Read ``SKILL.md`` and ``schema.json`` for the given skill.

        Returns a dict with keys ``skill_doc`` (str) and ``schema``
        (dict | None).
        """
        meta = self.registry.get_skill_by_name(skill_name)
        if meta is None:
            return {"error": f"Skill '{skill_name}' not found"}

        skill_doc = self._read_text(meta.directory / "SKILL.md")
        schema = self._read_json(meta.directory / "schema.json")

        return {
            "skill_doc": skill_doc,
            "schema": schema,
        }

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute_skill(self, skill_name: str, params: dict) -> dict[str, Any]:
        """Dynamically import and run a skill's ``execute(params)`` function.

        Returns the dict produced by the skill, or a dict with an ``error``
        key if something goes wrong.
        """
        meta = self.registry.get_skill_by_name(skill_name)
        if meta is None:
            return {"error": f"Skill '{skill_name}' not found"}

        entry = meta.directory / meta.entry_point
        if not entry.exists():
            return {"error": f"Entry point not found: {entry}"}

        try:
            module = self._import_module(skill_name, entry)
            execute_fn = getattr(module, "execute", None)
            if execute_fn is None:
                return {"error": f"Skill '{skill_name}' has no execute() function"}
            result = execute_fn(params)
            return result
        except Exception as exc:
            logger.exception("Skill '%s' execution failed", skill_name)
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _import_module(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(f"skill_{name}", str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _read_text(path: Path) -> Optional[str]:
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    @staticmethod
    def _read_json(path: Path) -> Optional[dict]:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in %s", path)
        return None
