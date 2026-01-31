"""Skill loader - Parse SKILL.md and discover skill files."""

import re
from pathlib import Path
from typing import Any

import frontmatter

from skillreadiness.core.models import Skill, SkillFile, SkillManifest


class SkillLoadError(Exception):
    """Error loading a skill package."""

    pass


class SkillLoader:
    """Load and parse skill packages from disk."""

    MAX_FILE_SIZE = 10 * 1024 * 1024
    SKIP_DIRS = {"__pycache__", ".git", ".venv", "node_modules", ".cursor"}
    SKIP_FILES = {".DS_Store", "Thumbs.db"}

    FILE_TYPE_MAP = {
        ".py": "python",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".js": "javascript",
        ".ts": "typescript",
        ".md": "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".txt": "text",
    }

    def load_skill(self, skill_directory: Path) -> Skill:
        """Load a skill from a directory."""
        if not skill_directory.is_dir():
            raise SkillLoadError(f"Not a directory: {skill_directory}")

        skill_md_path = skill_directory / "SKILL.md"
        if not skill_md_path.exists():
            raise SkillLoadError(f"SKILL.md not found in {skill_directory}")

        manifest, instruction_body = self._parse_skill_md(skill_md_path)
        files = self._discover_files(skill_directory)
        referenced_files = self._extract_referenced_files(instruction_body)

        return Skill(
            directory=skill_directory,
            manifest=manifest,
            skill_md_path=skill_md_path,
            instruction_body=instruction_body,
            files=files,
            referenced_files=referenced_files,
        )

    def _parse_skill_md(self, skill_md_path: Path) -> tuple[SkillManifest, str]:
        """Parse SKILL.md frontmatter and body."""
        try:
            content = skill_md_path.read_text(encoding="utf-8")
        except Exception as e:
            raise SkillLoadError(f"Failed to read SKILL.md: {e}") from e

        try:
            post = frontmatter.loads(content)
        except Exception as e:
            raise SkillLoadError(f"Failed to parse SKILL.md frontmatter: {e}") from e

        metadata = dict(post.metadata)
        manifest = self._build_manifest(metadata)
        instruction_body = post.content

        return manifest, instruction_body

    def _build_manifest(self, metadata: dict[str, Any]) -> SkillManifest:
        """Build SkillManifest from parsed metadata."""
        allowed_tools = metadata.get("allowed-tools") or metadata.get("allowed_tools")
        if isinstance(allowed_tools, str):
            allowed_tools = [t.strip() for t in allowed_tools.split(",")]

        disable_model = metadata.get("disable-model-invocation") or metadata.get(
            "disable_model_invocation", False
        )

        extra_metadata = {}
        known_fields = {
            "name",
            "description",
            "license",
            "compatibility",
            "allowed-tools",
            "allowed_tools",
            "disable-model-invocation",
            "disable_model_invocation",
            "metadata",
        }
        for key, value in metadata.items():
            if key not in known_fields:
                extra_metadata[key] = value

        combined_metadata = metadata.get("metadata", {})
        if extra_metadata:
            combined_metadata = {**combined_metadata, **extra_metadata}

        return SkillManifest(
            name=metadata.get("name"),
            description=metadata.get("description"),
            license=metadata.get("license"),
            compatibility=metadata.get("compatibility"),
            allowed_tools=allowed_tools,
            metadata=combined_metadata if combined_metadata else None,
            disable_model_invocation=bool(disable_model),
        )

    def _discover_files(self, directory: Path) -> list[SkillFile]:
        """Discover all files in the skill directory."""
        files: list[SkillFile] = []

        for path in directory.rglob("*"):
            if not path.is_file():
                continue

            if any(skip in path.parts for skip in self.SKIP_DIRS):
                continue

            if path.name in self.SKIP_FILES:
                continue

            relative_path = str(path.relative_to(directory))
            file_type = self._get_file_type(path)
            size_bytes = path.stat().st_size

            content = None
            if size_bytes <= self.MAX_FILE_SIZE and file_type not in ("binary", "unknown"):
                try:
                    content = path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, PermissionError):
                    file_type = "binary"

            files.append(
                SkillFile(
                    path=path,
                    relative_path=relative_path,
                    file_type=file_type,
                    content=content,
                    size_bytes=size_bytes,
                )
            )

        return files

    def _get_file_type(self, path: Path) -> str:
        """Determine file type from extension."""
        suffix = path.suffix.lower()
        return self.FILE_TYPE_MAP.get(suffix, "other")

    def _extract_referenced_files(self, content: str) -> list[str]:
        """Extract file references from markdown content."""
        references: set[str] = set()

        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        for match in re.finditer(link_pattern, content):
            ref = match.group(2)
            if not ref.startswith(("http://", "https://", "#")):
                references.add(ref)

        see_pattern = r"(?:see|refer to|check|read)\s+[`'\"]?([a-zA-Z0-9_\-./]+\.(?:md|py|sh|txt))[`'\"]?"
        for match in re.finditer(see_pattern, content, re.IGNORECASE):
            references.add(match.group(1))

        run_pattern = r"(?:run|execute|python|bash|sh)\s+[`'\"]?([a-zA-Z0-9_\-./]+\.(?:py|sh))[`'\"]?"
        for match in re.finditer(run_pattern, content, re.IGNORECASE):
            references.add(match.group(1))

        return sorted(references)


def load_skill(path: str | Path) -> Skill:
    """Convenience function to load a skill."""
    loader = SkillLoader()
    return loader.load_skill(Path(path))
