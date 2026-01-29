"""Skill tool - load a skill's instructions from SKILL.md."""

import json
from typing import Any, Callable, Dict, Optional

from ...base import Tool
from .skill_registry import SkillRegistry


PermissionChecker = Callable[[str], str]


class SkillTool(Tool):
    """
    A tool that lists and loads skills.

    Output is a JSON string (to match existing builtin tools in this repo).
    """

    def __init__(
        self,
        session,
        *,
        allow_global: bool = False,
        permission_checker: Optional[PermissionChecker] = None,
    ):
        super().__init__(session)
        self._registry = SkillRegistry(self.session.working_dir, allow_global=allow_global)
        self._permission_checker = permission_checker

    @property
    def name(self) -> str:
        return "skill"

    @property
    def description(self) -> str:
        skills = self._registry.all()
        allowed = [s for s in skills if self._is_allowed(s.name)]

        if not allowed:
            return (
                "Load a skill to get detailed instructions for a specific task. "
                "No skills are currently available."
            )

        parts = [
            "Load a skill to get detailed instructions for a specific task.",
            "Skills provide specialized knowledge and step-by-step guidance.",
            "Use this when a task matches an available skill's description.",
            "<available_skills>",
        ]
        for s in allowed:
            parts.extend(
                [
                    "  <skill>",
                    f"    <name>{s.name}</name>",
                    f"    <description>{s.description}</description>",
                    "  </skill>",
                ]
            )
        parts.append("</available_skills>")
        return " ".join(parts)

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The skill identifier from available_skills (e.g., 'code-review' or 'category/helper')",
                }
            },
            "required": ["name"],
        }

    def _is_allowed(self, skill_name: str) -> bool:
        if not self._permission_checker:
            return True
        try:
            action = self._permission_checker(skill_name)
        except Exception:
            return False
        return action != "deny"

    async def execute(self, **kwargs) -> str:
        name = (kwargs.get("name") or "").strip()
        if not name:
            return json.dumps({"error": "name parameter is required"}, ensure_ascii=False)

        if not self._is_allowed(name):
            return json.dumps({"error": f"Permission denied for skill '{name}'"}, ensure_ascii=False)

        skill = self._registry.get(name)
        if not skill:
            available = ", ".join([s.name for s in self._registry.all()])
            return json.dumps(
                {
                    "error": f'Skill "{name}" not found.',
                    "available": available or "none",
                },
                ensure_ascii=False,
            )

        try:
            raw = skill.location.read_text(encoding="utf-8")
        except Exception as e:
            return json.dumps(
                {"error": f"Failed to read skill file '{skill.location}': {e}"},
                ensure_ascii=False,
            )

        output = "\n".join(
            [
                f"## Skill: {skill.name}",
                "",
                f"**Base directory**: {str(skill.base_dir)}",
                "",
                raw.strip(),
            ]
        )

        resp = {
            "title": f"Loaded skill: {skill.name}",
            "output": output,
            "metadata": {"name": skill.name, "dir": str(skill.base_dir), "path": str(skill.location)},
        }

        warnings = self._registry.warnings()
        if warnings:
            resp["warnings"] = warnings
            resp["note"] = (
                "Some skills may be skipped due to missing/invalid frontmatter. "
                "Global (~/.claude/skills) scanning may also be blocked unless you whitelist it via allowed_paths."
            )

        return json.dumps(resp, ensure_ascii=False)


