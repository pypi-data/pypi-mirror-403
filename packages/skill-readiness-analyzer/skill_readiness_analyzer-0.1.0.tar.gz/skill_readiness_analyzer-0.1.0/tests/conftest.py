"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest

from skillreadiness.core.models import Skill, SkillFile, SkillManifest


@pytest.fixture
def temp_skill_dir():
    """Create a temporary skill directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_skill_md():
    """Return valid SKILL.md content."""
    return '''---
name: test-skill
description: A test skill for unit testing. Use when testing the analyzer.
license: MIT
---

# Test Skill

This is a test skill for unit testing.

## Instructions

Follow these instructions to use the skill.
'''


@pytest.fixture
def minimal_skill_md():
    """Return minimal valid SKILL.md content."""
    return '''---
name: minimal-skill
description: Minimal skill for testing. Use when you need a minimal test case.
---

# Minimal Skill

Basic content.
'''


@pytest.fixture
def invalid_skill_md():
    """Return SKILL.md with validation issues."""
    return '''---
name: InvalidName_With_Underscores
description: Short
---

# Bad Skill

I can help you with things.
'''


@pytest.fixture
def large_skill_md():
    """Return oversized SKILL.md content."""
    header = '''---
name: large-skill
description: A very large skill that exceeds recommended limits.
---

# Large Skill

'''
    body = "\n".join([f"Line {i}: Some content here." for i in range(600)])
    return header + body


@pytest.fixture
def sample_skill(temp_skill_dir, valid_skill_md):
    """Create a sample skill directory with valid content."""
    skill_md_path = temp_skill_dir / "SKILL.md"
    skill_md_path.write_text(valid_skill_md)
    return temp_skill_dir


@pytest.fixture
def sample_skill_with_scripts(temp_skill_dir, valid_skill_md):
    """Create a sample skill with Python and shell scripts."""
    skill_md_path = temp_skill_dir / "SKILL.md"
    skill_md_path.write_text(valid_skill_md)

    scripts_dir = temp_skill_dir / "scripts"
    scripts_dir.mkdir()

    py_script = scripts_dir / "helper.py"
    py_script.write_text('''#!/usr/bin/env python3
import sys

def main():
    print("Hello from helper")
    data = process_input(sys.argv[1])
    print(data)

def process_input(value):
    return value.upper()

if __name__ == "__main__":
    main()
''')

    sh_script = scripts_dir / "setup.sh"
    sh_script.write_text('''#!/bin/bash
echo "Setting up..."
mkdir -p output
cp input/* output/
echo "Done!"
''')

    return temp_skill_dir


@pytest.fixture
def skill_model():
    """Create a Skill model instance for testing."""
    return Skill(
        directory=Path("/test/skill"),
        manifest=SkillManifest(
            name="test-skill",
            description="A test skill for unit testing. Use when testing.",
        ),
        skill_md_path=Path("/test/skill/SKILL.md"),
        instruction_body="# Test\n\nSome content here.",
        files=[],
        referenced_files=[],
    )
