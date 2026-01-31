"""Heuristic provider - Core readiness checks based on best practices."""

import re
from collections import Counter

from skillreadiness.core.models import Finding, Severity, Skill, SkillReadinessCategory
from skillreadiness.providers.base import InspectionProvider

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class HeuristicProvider(InspectionProvider):
    """Provider that runs heuristic checks based on Cursor/Anthropic best practices."""

    MAX_LINES = 500
    MAX_TOKENS = 2000
    MIN_DESCRIPTION_LENGTH = 50
    MAX_INLINE_CODE_LINES = 50
    TRIGGER_PATTERNS = [
        r"\buse when\b",
        r"\bwhen the user\b",
        r"\bwhen working with\b",
        r"\bwhen you need\b",
        r"\bif the user\b",
        r"\bfor\s+\w+\s+tasks\b",
    ]
    FIRST_SECOND_PERSON_PATTERNS = [
        r"\bI can\b",
        r"\bI will\b",
        r"\bI am\b",
        r"\byou can\b",
        r"\byou will\b",
        r"\byou should\b",
        r"\byour\b",
    ]
    TERMINOLOGY_GROUPS = [
        ["api endpoint", "url", "route", "path", "uri"],
        ["field", "box", "element", "control", "input"],
        ["function", "method", "procedure", "routine"],
        ["file", "document", "asset", "resource"],
    ]

    @property
    def name(self) -> str:
        return "heuristic"

    @property
    def description(self) -> str:
        return "Heuristic analysis based on Anthropic/Cursor best practices"

    async def analyze(self, skill: Skill) -> list[Finding]:
        """Run all heuristic checks on the skill."""
        findings: list[Finding] = []

        findings.extend(self._check_skill_md_lines(skill))
        findings.extend(self._check_token_count(skill))
        findings.extend(self._check_file_references(skill))
        findings.extend(self._check_large_code_blocks(skill))
        findings.extend(self._check_description_trigger(skill))
        findings.extend(self._check_description_person(skill))
        findings.extend(self._check_description_length(skill))
        findings.extend(self._check_name_required(skill))
        findings.extend(self._check_description_required(skill))
        findings.extend(self._check_name_format(skill))
        findings.extend(self._check_reference_depth(skill))
        findings.extend(self._check_terminology_consistency(skill))
        findings.extend(self._check_conflicting_instructions(skill))
        findings.extend(self._check_python_error_handling(skill))
        findings.extend(self._check_shell_error_handling(skill))

        return findings

    def _check_skill_md_lines(self, skill: Skill) -> list[Finding]:
        """SRDNS-001: Check if SKILL.md exceeds 500 lines."""
        line_count = len(skill.instruction_body.splitlines())

        if line_count > self.MAX_LINES:
            return [
                Finding(
                    category=SkillReadinessCategory.TOKEN_FOOTPRINT,
                    severity=Severity.MEDIUM,
                    title="SKILL.md exceeds recommended length",
                    description=f"SKILL.md has {line_count} lines (recommended: <{self.MAX_LINES})",
                    location="SKILL.md",
                    evidence={"line_count": line_count, "max_recommended": self.MAX_LINES},
                    provider=self.name,
                    remediation="Use progressive disclosure with file references to reduce size",
                    rule_id="SRDNS-001",
                )
            ]
        return []

    def _check_token_count(self, skill: Skill) -> list[Finding]:
        """SRDNS-002: Check if estimated tokens exceed 2000."""
        if not TIKTOKEN_AVAILABLE:
            return []

        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            full_content = f"{skill.manifest.description or ''}\n{skill.instruction_body}"
            token_count = len(encoding.encode(full_content))
        except Exception:
            return []

        if token_count > self.MAX_TOKENS:
            return [
                Finding(
                    category=SkillReadinessCategory.TOKEN_FOOTPRINT,
                    severity=Severity.MEDIUM,
                    title="SKILL.md exceeds recommended token count",
                    description=f"Estimated {token_count} tokens (recommended: <{self.MAX_TOKENS})",
                    location="SKILL.md",
                    evidence={"token_count": token_count, "max_recommended": self.MAX_TOKENS},
                    provider=self.name,
                    remediation="Split detailed content into referenced files",
                    rule_id="SRDNS-002",
                )
            ]
        return []

    def _check_file_references(self, skill: Skill) -> list[Finding]:
        """SRDNS-003: Check if skill uses progressive disclosure via file references."""
        line_count = len(skill.instruction_body.splitlines())

        if line_count > 100 and not skill.referenced_files:
            return [
                Finding(
                    category=SkillReadinessCategory.PROGRESSIVE_DISCLOSURE,
                    severity=Severity.MEDIUM,
                    title="No progressive disclosure utilized",
                    description="Large skill with no file references found",
                    location="SKILL.md",
                    evidence={"line_count": line_count, "referenced_files": []},
                    provider=self.name,
                    remediation="Consider splitting detailed content into reference.md or examples.md",
                    rule_id="SRDNS-003",
                )
            ]
        return []

    def _check_large_code_blocks(self, skill: Skill) -> list[Finding]:
        """SRDNS-004: Check for large inline code blocks."""
        findings: list[Finding] = []

        code_block_pattern = r"```[\w]*\n(.*?)```"
        for match in re.finditer(code_block_pattern, skill.instruction_body, re.DOTALL):
            block_content = match.group(1)
            block_lines = len(block_content.splitlines())

            if block_lines > self.MAX_INLINE_CODE_LINES:
                start_pos = match.start()
                line_num = skill.instruction_body[:start_pos].count("\n") + 1

                findings.append(
                    Finding(
                        category=SkillReadinessCategory.PROGRESSIVE_DISCLOSURE,
                        severity=Severity.LOW,
                        title="Large code block inline",
                        description=f"Code block with {block_lines} lines (recommended: <{self.MAX_INLINE_CODE_LINES})",
                        location=f"SKILL.md:{line_num}",
                        evidence={"block_lines": block_lines, "max_recommended": self.MAX_INLINE_CODE_LINES},
                        provider=self.name,
                        remediation="Move large code blocks to separate script files",
                        rule_id="SRDNS-004",
                    )
                )

        return findings

    def _check_description_trigger(self, skill: Skill) -> list[Finding]:
        """SRDNS-005: Check if description includes activation context."""
        description = skill.manifest.description or ""

        has_trigger = any(
            re.search(pattern, description, re.IGNORECASE) for pattern in self.TRIGGER_PATTERNS
        )

        if description and not has_trigger:
            return [
                Finding(
                    category=SkillReadinessCategory.DESCRIPTION_QUALITY,
                    severity=Severity.HIGH,
                    title="Description missing activation context",
                    description='Description lacks "Use when..." clause or similar trigger context',
                    location="SKILL.md:description",
                    evidence={"description": description[:200]},
                    provider=self.name,
                    remediation='Add activation context like "Use when working with PDF files"',
                    rule_id="SRDNS-005",
                )
            ]
        return []

    def _check_description_person(self, skill: Skill) -> list[Finding]:
        """SRDNS-006: Check if description uses third person."""
        description = skill.manifest.description or ""

        for pattern in self.FIRST_SECOND_PERSON_PATTERNS:
            if re.search(pattern, description, re.IGNORECASE):
                return [
                    Finding(
                        category=SkillReadinessCategory.DESCRIPTION_QUALITY,
                        severity=Severity.MEDIUM,
                        title="Description uses first/second person",
                        description="Description should be written in third person",
                        location="SKILL.md:description",
                        evidence={"description": description[:200], "matched_pattern": pattern},
                        provider=self.name,
                        remediation='Use third person: "Processes files" not "I can process files"',
                        rule_id="SRDNS-006",
                    )
                ]
        return []

    def _check_description_length(self, skill: Skill) -> list[Finding]:
        """SRDNS-007: Check if description is too short/vague."""
        description = skill.manifest.description or ""

        if description and len(description) < self.MIN_DESCRIPTION_LENGTH:
            return [
                Finding(
                    category=SkillReadinessCategory.DESCRIPTION_QUALITY,
                    severity=Severity.HIGH,
                    title="Description too short",
                    description=f"Description is {len(description)} chars (recommended: >{self.MIN_DESCRIPTION_LENGTH})",
                    location="SKILL.md:description",
                    evidence={"description": description, "length": len(description)},
                    provider=self.name,
                    remediation="Add specific details about what the skill does and when to use it",
                    rule_id="SRDNS-007",
                )
            ]
        return []

    def _check_name_required(self, skill: Skill) -> list[Finding]:
        """SRDNS-008: Check if name field exists."""
        if not skill.manifest.name:
            return [
                Finding(
                    category=SkillReadinessCategory.METADATA_VALIDATION,
                    severity=Severity.HIGH,
                    title="Missing required name field",
                    description="SKILL.md frontmatter must include a name field",
                    location="SKILL.md:frontmatter",
                    evidence={},
                    provider=self.name,
                    remediation="Add name field to frontmatter: name: your-skill-name",
                    rule_id="SRDNS-008",
                )
            ]
        return []

    def _check_description_required(self, skill: Skill) -> list[Finding]:
        """SRDNS-009: Check if description field exists."""
        if not skill.manifest.description:
            return [
                Finding(
                    category=SkillReadinessCategory.METADATA_VALIDATION,
                    severity=Severity.HIGH,
                    title="Missing required description field",
                    description="SKILL.md frontmatter must include a description field",
                    location="SKILL.md:frontmatter",
                    evidence={},
                    provider=self.name,
                    remediation="Add description field explaining what the skill does and when to use it",
                    rule_id="SRDNS-009",
                )
            ]
        return []

    def _check_name_format(self, skill: Skill) -> list[Finding]:
        """SRDNS-010: Check if name follows format rules."""
        name = skill.manifest.name
        if not name:
            return []

        name_pattern = r"^[a-z][a-z0-9-]*$"

        issues = []
        if len(name) > 64:
            issues.append(f"exceeds 64 chars ({len(name)})")
        if not re.match(name_pattern, name):
            issues.append("must be lowercase letters, numbers, and hyphens only")

        if issues:
            return [
                Finding(
                    category=SkillReadinessCategory.METADATA_VALIDATION,
                    severity=Severity.MEDIUM,
                    title="Invalid name format",
                    description=f"Name '{name}' {'; '.join(issues)}",
                    location="SKILL.md:name",
                    evidence={"name": name, "issues": issues},
                    provider=self.name,
                    remediation="Use lowercase letters, numbers, and hyphens; max 64 chars",
                    rule_id="SRDNS-010",
                )
            ]
        return []

    def _check_reference_depth(self, skill: Skill) -> list[Finding]:
        """SRDNS-011: Check for nested references (references to references)."""
        if not skill.referenced_files:
            return []

        nested_refs: list[str] = []
        for ref_file in skill.referenced_files:
            for skill_file in skill.files:
                if skill_file.relative_path == ref_file and skill_file.content:
                    link_pattern = r"\[([^\]]+)\]\(([^)]+\.md)\)"
                    if re.search(link_pattern, skill_file.content):
                        nested_refs.append(ref_file)
                        break

        if nested_refs:
            return [
                Finding(
                    category=SkillReadinessCategory.REFERENCE_DEPTH,
                    severity=Severity.LOW,
                    title="Nested references detected",
                    description="Referenced files contain further markdown references",
                    location="SKILL.md",
                    evidence={"files_with_nested_refs": nested_refs},
                    provider=self.name,
                    remediation="Keep references one level deep from SKILL.md",
                    rule_id="SRDNS-011",
                )
            ]
        return []

    def _check_terminology_consistency(self, skill: Skill) -> list[Finding]:
        """SRDNS-012: Check for mixed terminology."""
        full_content = f"{skill.manifest.description or ''}\n{skill.instruction_body}"
        content_lower = full_content.lower()

        for term_group in self.TERMINOLOGY_GROUPS:
            found_terms: list[str] = []
            for term in term_group:
                if term in content_lower:
                    found_terms.append(term)

            if len(found_terms) > 1:
                return [
                    Finding(
                        category=SkillReadinessCategory.TERMINOLOGY_CONSISTENCY,
                        severity=Severity.LOW,
                        title="Mixed terminology detected",
                        description=f"Multiple terms used for same concept: {', '.join(found_terms)}",
                        location="SKILL.md",
                        evidence={"found_terms": found_terms, "term_group": term_group},
                        provider=self.name,
                        remediation="Choose one term and use it consistently throughout",
                        rule_id="SRDNS-012",
                    )
                ]
        return []

    def _check_conflicting_instructions(self, skill: Skill) -> list[Finding]:
        """SRDNS-013: Check for conflicting instruction patterns."""
        content = skill.instruction_body

        conflict_patterns = [
            (r"\buse\s+(\w+)\b.*?\bdon't use\s+\1\b", "contradictory use/don't use"),
            (r"\balways\b.*?\bsometimes\b", "mixed always/sometimes"),
            (r"\bnever\b.*?\bcan\b.*?\bif\b", "exception to never"),
            (r"\byou can use\s+(\w+).*?or\s+(\w+).*?or\s+(\w+)", "too many options"),
        ]

        for pattern, desc in conflict_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                return [
                    Finding(
                        category=SkillReadinessCategory.INSTRUCTION_CLARITY,
                        severity=Severity.MEDIUM,
                        title="Potentially conflicting instructions",
                        description=f"Pattern detected: {desc}",
                        location="SKILL.md",
                        evidence={"pattern_type": desc},
                        provider=self.name,
                        remediation="Provide clear defaults and explicit exceptions",
                        rule_id="SRDNS-013",
                    )
                ]
        return []

    def _check_python_error_handling(self, skill: Skill) -> list[Finding]:
        """SRDNS-014: Check Python scripts for error handling."""
        findings: list[Finding] = []

        for skill_file in skill.files:
            if skill_file.file_type != "python" or not skill_file.content:
                continue

            if skill_file.relative_path == "SKILL.md":
                continue

            has_try_except = "try:" in skill_file.content and "except" in skill_file.content

            if not has_try_except and len(skill_file.content.splitlines()) > 20:
                findings.append(
                    Finding(
                        category=SkillReadinessCategory.SCRIPT_RELIABILITY,
                        severity=Severity.MEDIUM,
                        title="Python script missing error handling",
                        description="Script lacks try/except blocks for error handling",
                        location=skill_file.relative_path,
                        evidence={"file": skill_file.relative_path},
                        provider=self.name,
                        remediation="Add try/except blocks to handle potential errors",
                        rule_id="SRDNS-014",
                    )
                )

        return findings

    def _check_shell_error_handling(self, skill: Skill) -> list[Finding]:
        """SRDNS-015: Check shell scripts for error handling."""
        findings: list[Finding] = []

        for skill_file in skill.files:
            if skill_file.file_type != "bash" or not skill_file.content:
                continue

            has_set_e = "set -e" in skill_file.content or "set -o errexit" in skill_file.content

            if not has_set_e and len(skill_file.content.splitlines()) > 10:
                findings.append(
                    Finding(
                        category=SkillReadinessCategory.SCRIPT_RELIABILITY,
                        severity=Severity.MEDIUM,
                        title="Shell script missing error handling",
                        description='Script lacks "set -e" for fail-fast behavior',
                        location=skill_file.relative_path,
                        evidence={"file": skill_file.relative_path},
                        provider=self.name,
                        remediation='Add "set -e" at the start of the script',
                        rule_id="SRDNS-015",
                    )
                )

        return findings
