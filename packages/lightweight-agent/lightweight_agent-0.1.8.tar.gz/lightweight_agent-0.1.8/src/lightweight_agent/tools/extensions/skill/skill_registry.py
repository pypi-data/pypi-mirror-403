from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


@dataclass(frozen=True)
class SkillInfo:
    name: str
    description: str
    location: Path

    @property
    def base_dir(self) -> Path:
        return self.location.parent


class SkillRegistry:
    """
    Discovers skills from directories compatible with Claude/OpenCode conventions.

    IMPORTANT: In lightweight-agent, tools are generally restricted to paths inside Session.working_dir
    unless the user explicitly whitelists more paths via allowed_paths. This registry therefore:
    - Always scans under `project_root` (usually session.working_dir)
    - Optionally scans global home (~/.claude/skills) ONLY if `allow_global=True` and the path is allowed.
    """

    def __init__(self, project_root: Path, allow_global: bool = False):
        self.project_root = Path(project_root).resolve()
        self.allow_global = allow_global
        self._cache: Optional[Dict[str, SkillInfo]] = None
        self._warnings: List[str] = []

    def refresh(self) -> None:
        self._cache = None
        self._warnings = []

    def warnings(self) -> List[str]:
        # Return a copy so callers don't mutate internal state
        return list(self._warnings)

    def all(self) -> List[SkillInfo]:
        skills = self._ensure_loaded()
        return sorted(skills.values(), key=lambda s: s.name)

    def get(self, name: str) -> Optional[SkillInfo]:
        return self._ensure_loaded().get(name)

    def _ensure_loaded(self) -> Dict[str, SkillInfo]:
        if self._cache is not None:
            return self._cache
        self._cache = self._scan()
        return self._cache

    def _scan(self) -> Dict[str, SkillInfo]:
        found: Dict[str, SkillInfo] = {}
        self._warnings = []

        for md_path in self._iter_skill_files():
            info = self._parse_skill_file(md_path)
            if info is None:
                continue

            if info.name in found:
                self._warnings.append(
                    f"Duplicate skill name '{info.name}' found at '{md_path}'. "
                    f"Overriding previous definition at '{found[info.name].location}'."
                )
            found[info.name] = info

        return found

    def _iter_skill_files(self) -> List[Path]:
        candidates: List[Path] = []

        # Project-local paths
        candidates.extend(self._glob_under(self.project_root / ".claude" / "skills"))
        candidates.extend(self._glob_under(self.project_root / ".opencode" / "skill"))
        candidates.extend(self._glob_under(self.project_root / ".opencode" / "skills"))

        # Global home path (optional; may be blocked by the framework)
        if self.allow_global:
            home = Path.home()
            candidates.extend(self._glob_under(home / ".claude" / "skills"))

        # Deduplicate preserving order
        seen = set()
        unique: List[Path] = []
        for p in candidates:
            rp = str(p.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            unique.append(p)
        return unique

    @staticmethod
    def _glob_under(root: Path) -> List[Path]:
        if not root.exists() or not root.is_dir():
            return []
        # Convention: any subdirectory can contain SKILL.md
        return sorted(root.glob("**/SKILL.md"))

    def _parse_skill_file(self, file_path: Path) -> Optional[SkillInfo]:
        try:
            raw = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self._warnings.append(f"Failed to read skill file '{file_path}': {e}")
            return None

        fm_text, _body = self._split_frontmatter(raw)
        if fm_text is None:
            self._warnings.append(f"Skipping '{file_path}': missing YAML frontmatter (--- ... ---).")
            return None

        try:
            data = yaml.safe_load(fm_text) or {}
        except Exception as e:
            self._warnings.append(f"Skipping '{file_path}': failed to parse YAML frontmatter: {e}")
            return None

        name = (data.get("name") or "").strip()
        desc = (data.get("description") or "").strip()
        if not name or not desc:
            self._warnings.append(
                f"Skipping '{file_path}': frontmatter must include non-empty 'name' and 'description'."
            )
            return None

        return SkillInfo(name=name, description=desc, location=file_path.resolve())

    @staticmethod
    def _split_frontmatter(content: str) -> Tuple[Optional[str], str]:
        """
        Returns (frontmatter_text_without_delimiters, body).
        If missing, returns (None, original_content).
        """
        # Support both \n and \r\n
        if not content.startswith("---"):
            return None, content

        # Find the second delimiter line
        # A minimal frontmatter is:
        # ---
        # key: value
        # ---
        # body...
        lines = content.splitlines(True)
        if not lines:
            return None, content
        if not lines[0].lstrip().startswith("---"):
            return None, content

        # Accumulate until the next '---' line
        fm_lines: List[str] = []
        i = 1
        while i < len(lines):
            line = lines[i]
            if line.strip() == "---":
                body = "".join(lines[i + 1 :])
                return "".join(fm_lines), body
            fm_lines.append(line)
            i += 1

        return None, content


