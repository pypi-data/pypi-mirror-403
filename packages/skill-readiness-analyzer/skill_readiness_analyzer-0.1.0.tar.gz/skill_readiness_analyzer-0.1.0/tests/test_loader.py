"""Tests for skill loader."""

from pathlib import Path

import pytest

from skillreadiness.core.loader import SkillLoader, SkillLoadError, load_skill


class TestSkillLoader:
    def test_load_valid_skill(self, sample_skill):
        loader = SkillLoader()
        skill = loader.load_skill(sample_skill)

        assert skill.name == "test-skill"
        assert skill.manifest.description is not None
        assert "Use when testing" in skill.manifest.description
        assert skill.manifest.license == "MIT"

    def test_load_skill_with_scripts(self, sample_skill_with_scripts):
        loader = SkillLoader()
        skill = loader.load_skill(sample_skill_with_scripts)

        assert skill.name == "test-skill"
        assert len(skill.files) >= 3

        file_types = {f.file_type for f in skill.files}
        assert "python" in file_types
        assert "bash" in file_types

    def test_load_missing_skill_md(self, temp_skill_dir):
        loader = SkillLoader()
        with pytest.raises(SkillLoadError) as exc:
            loader.load_skill(temp_skill_dir)
        assert "SKILL.md not found" in str(exc.value)

    def test_load_not_directory(self, temp_skill_dir):
        file_path = temp_skill_dir / "somefile.txt"
        file_path.write_text("content")

        loader = SkillLoader()
        with pytest.raises(SkillLoadError) as exc:
            loader.load_skill(file_path)
        assert "Not a directory" in str(exc.value)

    def test_parse_frontmatter(self, temp_skill_dir, valid_skill_md):
        skill_md_path = temp_skill_dir / "SKILL.md"
        skill_md_path.write_text(valid_skill_md)

        loader = SkillLoader()
        skill = loader.load_skill(temp_skill_dir)

        assert skill.manifest.name == "test-skill"
        assert skill.manifest.license == "MIT"

    def test_extract_referenced_files(self, temp_skill_dir):
        content = '''---
name: ref-test
description: Test skill with references. Use when testing references.
---

# Reference Test

See [reference.md](reference.md) for details.
Also check examples.md for examples.
Run python scripts/helper.py for help.
'''
        skill_md_path = temp_skill_dir / "SKILL.md"
        skill_md_path.write_text(content)

        loader = SkillLoader()
        skill = loader.load_skill(temp_skill_dir)

        assert "reference.md" in skill.referenced_files
        assert "examples.md" in skill.referenced_files
        assert "scripts/helper.py" in skill.referenced_files

    def test_convenience_function(self, sample_skill):
        skill = load_skill(sample_skill)
        assert skill.name == "test-skill"


class TestAllowedToolsParsing:
    def test_allowed_tools_as_list(self, temp_skill_dir):
        content = '''---
name: tools-test
description: Test allowed tools parsing. Use when testing.
allowed-tools:
  - Read
  - Write
  - Shell
---

# Tools Test
'''
        (temp_skill_dir / "SKILL.md").write_text(content)

        loader = SkillLoader()
        skill = loader.load_skill(temp_skill_dir)

        assert skill.manifest.allowed_tools == ["Read", "Write", "Shell"]

    def test_allowed_tools_as_string(self, temp_skill_dir):
        content = '''---
name: tools-test
description: Test allowed tools parsing. Use when testing.
allowed-tools: Read, Write, Shell
---

# Tools Test
'''
        (temp_skill_dir / "SKILL.md").write_text(content)

        loader = SkillLoader()
        skill = loader.load_skill(temp_skill_dir)

        assert skill.manifest.allowed_tools == ["Read", "Write", "Shell"]

    def test_allowed_tools_snake_case(self, temp_skill_dir):
        content = '''---
name: tools-test
description: Test allowed tools parsing. Use when testing.
allowed_tools:
  - Read
  - Write
---

# Tools Test
'''
        (temp_skill_dir / "SKILL.md").write_text(content)

        loader = SkillLoader()
        skill = loader.load_skill(temp_skill_dir)

        assert skill.manifest.allowed_tools == ["Read", "Write"]
