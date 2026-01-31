"""Tests for heuristic provider."""

from pathlib import Path

import pytest

from skillreadiness.core.loader import load_skill
from skillreadiness.core.models import Severity, Skill, SkillFile, SkillManifest, SkillReadinessCategory
from skillreadiness.providers.heuristic_provider import HeuristicProvider


@pytest.fixture
def provider():
    return HeuristicProvider()


def make_skill(
    name: str = "test-skill",
    description: str = "Test skill description. Use when testing the provider.",
    instruction_body: str = "# Test\n\nContent here.",
    files: list | None = None,
    referenced_files: list | None = None,
) -> Skill:
    return Skill(
        directory=Path("/test"),
        manifest=SkillManifest(name=name, description=description),
        skill_md_path=Path("/test/SKILL.md"),
        instruction_body=instruction_body,
        files=files or [],
        referenced_files=referenced_files or [],
    )


class TestLineCountCheck:
    @pytest.mark.asyncio
    async def test_within_limits(self, provider):
        skill = make_skill(instruction_body="\n".join(["Line"] * 100))
        findings = await provider.analyze(skill)
        line_findings = [f for f in findings if f.rule_id == "SRDNS-001"]
        assert len(line_findings) == 0

    @pytest.mark.asyncio
    async def test_exceeds_limits(self, provider):
        skill = make_skill(instruction_body="\n".join(["Line"] * 600))
        findings = await provider.analyze(skill)
        line_findings = [f for f in findings if f.rule_id == "SRDNS-001"]
        assert len(line_findings) == 1
        assert line_findings[0].severity == Severity.MEDIUM


class TestDescriptionQuality:
    @pytest.mark.asyncio
    async def test_missing_trigger(self, provider):
        skill = make_skill(description="A skill that does things with files.")
        findings = await provider.analyze(skill)
        trigger_findings = [f for f in findings if f.rule_id == "SRDNS-005"]
        assert len(trigger_findings) == 1
        assert trigger_findings[0].severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_has_trigger(self, provider):
        skill = make_skill(description="Process PDF files. Use when working with PDFs.")
        findings = await provider.analyze(skill)
        trigger_findings = [f for f in findings if f.rule_id == "SRDNS-005"]
        assert len(trigger_findings) == 0

    @pytest.mark.asyncio
    async def test_first_person(self, provider):
        skill = make_skill(description="I can help you process files. Use when needed.")
        findings = await provider.analyze(skill)
        person_findings = [f for f in findings if f.rule_id == "SRDNS-006"]
        assert len(person_findings) == 1

    @pytest.mark.asyncio
    async def test_third_person(self, provider):
        skill = make_skill(description="Processes files and generates reports. Use when analyzing data.")
        findings = await provider.analyze(skill)
        person_findings = [f for f in findings if f.rule_id == "SRDNS-006"]
        assert len(person_findings) == 0

    @pytest.mark.asyncio
    async def test_short_description(self, provider):
        skill = make_skill(description="Short desc")
        findings = await provider.analyze(skill)
        length_findings = [f for f in findings if f.rule_id == "SRDNS-007"]
        assert len(length_findings) == 1
        assert length_findings[0].severity == Severity.HIGH


class TestMetadataValidation:
    @pytest.mark.asyncio
    async def test_missing_name(self, provider):
        skill = make_skill(name=None)
        findings = await provider.analyze(skill)
        name_findings = [f for f in findings if f.rule_id == "SRDNS-008"]
        assert len(name_findings) == 1

    @pytest.mark.asyncio
    async def test_missing_description(self, provider):
        skill = make_skill(description=None)
        findings = await provider.analyze(skill)
        desc_findings = [f for f in findings if f.rule_id == "SRDNS-009"]
        assert len(desc_findings) == 1

    @pytest.mark.asyncio
    async def test_invalid_name_format(self, provider):
        skill = make_skill(name="Invalid_Name_Here")
        findings = await provider.analyze(skill)
        format_findings = [f for f in findings if f.rule_id == "SRDNS-010"]
        assert len(format_findings) == 1

    @pytest.mark.asyncio
    async def test_valid_name_format(self, provider):
        skill = make_skill(name="valid-skill-name")
        findings = await provider.analyze(skill)
        format_findings = [f for f in findings if f.rule_id == "SRDNS-010"]
        assert len(format_findings) == 0


class TestProgressiveDisclosure:
    @pytest.mark.asyncio
    async def test_large_without_refs(self, provider):
        skill = make_skill(
            instruction_body="\n".join(["Content line"] * 150),
            referenced_files=[],
        )
        findings = await provider.analyze(skill)
        disclosure_findings = [f for f in findings if f.rule_id == "SRDNS-003"]
        assert len(disclosure_findings) == 1

    @pytest.mark.asyncio
    async def test_large_with_refs(self, provider):
        skill = make_skill(
            instruction_body="\n".join(["Content line"] * 150),
            referenced_files=["reference.md"],
        )
        findings = await provider.analyze(skill)
        disclosure_findings = [f for f in findings if f.rule_id == "SRDNS-003"]
        assert len(disclosure_findings) == 0

    @pytest.mark.asyncio
    async def test_large_code_block(self, provider):
        code_block = "```python\n" + "\n".join([f"line_{i} = {i}" for i in range(60)]) + "\n```"
        skill = make_skill(instruction_body=f"# Test\n\n{code_block}")
        findings = await provider.analyze(skill)
        block_findings = [f for f in findings if f.rule_id == "SRDNS-004"]
        assert len(block_findings) == 1


class TestScriptReliability:
    @pytest.mark.asyncio
    async def test_python_without_error_handling(self, provider):
        py_content = '''#!/usr/bin/env python3
import sys
import os
import json
import logging

logger = logging.getLogger(__name__)

def main():
    data = open(sys.argv[1]).read()
    result = process(data)
    print(result)
    save_output(result)

def process(data):
    lines = data.split("\\n")
    processed = []
    for line in lines:
        processed.append(line.upper())
    return "\\n".join(processed)

def save_output(result):
    with open("output.txt", "w") as f:
        f.write(result)

if __name__ == "__main__":
    main()
'''
        skill = make_skill(
            files=[
                SkillFile(
                    path=Path("/test/scripts/helper.py"),
                    relative_path="scripts/helper.py",
                    file_type="python",
                    content=py_content,
                    size_bytes=len(py_content),
                )
            ]
        )
        findings = await provider.analyze(skill)
        py_findings = [f for f in findings if f.rule_id == "SRDNS-014"]
        assert len(py_findings) == 1

    @pytest.mark.asyncio
    async def test_python_with_error_handling(self, provider):
        py_content = '''#!/usr/bin/env python3
import sys

def main():
    try:
        data = open(sys.argv[1]).read()
        result = process(data)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def process(data):
    return data.upper()

if __name__ == "__main__":
    main()
'''
        skill = make_skill(
            files=[
                SkillFile(
                    path=Path("/test/scripts/helper.py"),
                    relative_path="scripts/helper.py",
                    file_type="python",
                    content=py_content,
                    size_bytes=len(py_content),
                )
            ]
        )
        findings = await provider.analyze(skill)
        py_findings = [f for f in findings if f.rule_id == "SRDNS-014"]
        assert len(py_findings) == 0

    @pytest.mark.asyncio
    async def test_shell_without_set_e(self, provider):
        sh_content = '''#!/bin/bash
echo "Starting..."
mkdir -p output
cp input/* output/
echo "Processing files..."
for f in output/*; do
    echo "Processing $f"
    cat "$f" >> combined.txt
done
echo "Cleaning up..."
rm -rf temp/
echo "Done!"
'''
        skill = make_skill(
            files=[
                SkillFile(
                    path=Path("/test/scripts/setup.sh"),
                    relative_path="scripts/setup.sh",
                    file_type="bash",
                    content=sh_content,
                    size_bytes=len(sh_content),
                )
            ]
        )
        findings = await provider.analyze(skill)
        sh_findings = [f for f in findings if f.rule_id == "SRDNS-015"]
        assert len(sh_findings) == 1

    @pytest.mark.asyncio
    async def test_shell_with_set_e(self, provider):
        sh_content = '''#!/bin/bash
set -e
echo "Starting..."
mkdir -p output
cp input/* output/
echo "Done!"
'''
        skill = make_skill(
            files=[
                SkillFile(
                    path=Path("/test/scripts/setup.sh"),
                    relative_path="scripts/setup.sh",
                    file_type="bash",
                    content=sh_content,
                    size_bytes=len(sh_content),
                )
            ]
        )
        findings = await provider.analyze(skill)
        sh_findings = [f for f in findings if f.rule_id == "SRDNS-015"]
        assert len(sh_findings) == 0
