"""Tests for core models."""

from datetime import datetime

import pytest

from skillreadiness.core.models import (
    Finding,
    ScanResult,
    Severity,
    Skill,
    SkillFile,
    SkillManifest,
    SkillReadinessCategory,
)


class TestSeverity:
    def test_severity_values(self):
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"

    def test_severity_ordering(self):
        severities = [Severity.LOW, Severity.CRITICAL, Severity.MEDIUM]
        sorted_sevs = sorted(severities, key=lambda s: s.value)
        assert sorted_sevs[0] == Severity.CRITICAL


class TestSkillReadinessCategory:
    def test_all_categories_exist(self):
        expected = [
            "token-footprint",
            "progressive-disclosure",
            "description-quality",
            "platform-compatibility",
            "dependency-completeness",
            "instruction-clarity",
            "metadata-validation",
            "reference-depth",
            "terminology-consistency",
            "script-reliability",
        ]
        actual = [c.value for c in SkillReadinessCategory]
        assert sorted(actual) == sorted(expected)


class TestSkillManifest:
    def test_minimal_manifest(self):
        manifest = SkillManifest()
        assert manifest.name is None
        assert manifest.description is None
        assert manifest.allowed_tools is None

    def test_full_manifest(self):
        manifest = SkillManifest(
            name="test-skill",
            description="A test skill",
            license="MIT",
            compatibility="cursor",
            allowed_tools=["Read", "Write"],
            metadata={"author": "test"},
            disable_model_invocation=True,
        )
        assert manifest.name == "test-skill"
        assert manifest.license == "MIT"
        assert len(manifest.allowed_tools) == 2
        assert manifest.disable_model_invocation is True


class TestFinding:
    def test_finding_creation(self):
        finding = Finding(
            category=SkillReadinessCategory.DESCRIPTION_QUALITY,
            severity=Severity.HIGH,
            title="Test finding",
            description="A test finding description",
            provider="test",
            rule_id="TEST-001",
        )
        assert finding.category == SkillReadinessCategory.DESCRIPTION_QUALITY
        assert finding.severity == Severity.HIGH
        assert finding.rule_id == "TEST-001"

    def test_finding_with_evidence(self):
        finding = Finding(
            category=SkillReadinessCategory.TOKEN_FOOTPRINT,
            severity=Severity.MEDIUM,
            title="Large skill",
            description="Skill exceeds size limits",
            location="SKILL.md",
            evidence={"line_count": 600, "max": 500},
            provider="heuristic",
            remediation="Reduce size",
            rule_id="SRDNS-001",
        )
        assert finding.evidence["line_count"] == 600
        assert finding.location == "SKILL.md"


class TestScanResult:
    def test_empty_scan_result(self):
        result = ScanResult(
            skill_name="test",
            skill_directory="/test",
        )
        assert result.readiness_score == 100
        assert result.is_production_ready is True
        assert result.readiness_label == "Production Ready"
        assert len(result.findings) == 0

    def test_scan_result_with_findings(self):
        findings = [
            Finding(
                category=SkillReadinessCategory.DESCRIPTION_QUALITY,
                severity=Severity.HIGH,
                title="Test",
                description="Test",
                provider="test",
            ),
            Finding(
                category=SkillReadinessCategory.TOKEN_FOOTPRINT,
                severity=Severity.MEDIUM,
                title="Test2",
                description="Test2",
                provider="test",
            ),
        ]
        result = ScanResult(
            skill_name="test",
            skill_directory="/test",
            findings=findings,
            readiness_score=77,
        )
        assert result.has_high_findings is True
        assert result.has_critical_findings is False
        assert result.readiness_label == "Needs Improvement"

    def test_finding_counts(self):
        findings = [
            Finding(
                category=SkillReadinessCategory.DESCRIPTION_QUALITY,
                severity=Severity.HIGH,
                title="High1",
                description="Test",
                provider="test",
            ),
            Finding(
                category=SkillReadinessCategory.DESCRIPTION_QUALITY,
                severity=Severity.HIGH,
                title="High2",
                description="Test",
                provider="test",
            ),
            Finding(
                category=SkillReadinessCategory.TOKEN_FOOTPRINT,
                severity=Severity.MEDIUM,
                title="Medium",
                description="Test",
                provider="test",
            ),
        ]
        result = ScanResult(
            skill_name="test",
            skill_directory="/test",
            findings=findings,
        )
        counts = result.finding_counts_by_severity
        assert counts["high"] == 2
        assert counts["medium"] == 1
        assert counts["low"] == 0

    def test_readiness_labels(self):
        assert ScanResult(skill_name="t", skill_directory="/", readiness_score=95).readiness_label == "Production Ready"
        assert ScanResult(skill_name="t", skill_directory="/", readiness_score=75).readiness_label == "Needs Improvement"
        assert ScanResult(skill_name="t", skill_directory="/", readiness_score=55).readiness_label == "Significant Issues"
        assert ScanResult(skill_name="t", skill_directory="/", readiness_score=30).readiness_label == "Not Ready"
