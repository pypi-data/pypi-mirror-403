"""Tests for readiness orchestrator."""

import pytest

from skillreadiness.core.models import Finding, Severity, SkillReadinessCategory
from skillreadiness.core.orchestrator import ReadinessOrchestrator, get_orchestrator
from skillreadiness.providers import HeuristicProvider


class TestReadinessOrchestrator:
    def test_create_orchestrator(self):
        orchestrator = ReadinessOrchestrator()
        assert orchestrator.providers == []
        assert orchestrator.timeout_seconds == 30.0

    def test_add_provider(self):
        orchestrator = ReadinessOrchestrator()
        provider = HeuristicProvider()
        orchestrator.add_provider(provider)
        assert len(orchestrator.providers) == 1

    @pytest.mark.asyncio
    async def test_scan_valid_skill(self, sample_skill):
        orchestrator = get_orchestrator()
        result = await orchestrator.scan_skill(sample_skill)

        assert result.skill_name == "test-skill"
        assert result.readiness_score >= 0
        assert result.readiness_score <= 100
        assert "heuristic" in result.providers_used

    @pytest.mark.asyncio
    async def test_scan_missing_skill(self, temp_skill_dir):
        orchestrator = get_orchestrator()
        result = await orchestrator.scan_skill(temp_skill_dir)

        assert result.readiness_score == 0
        assert len(result.findings) == 1
        assert result.findings[0].rule_id == "LOAD-ERROR"

    def test_scan_skill_sync(self, sample_skill):
        orchestrator = get_orchestrator()
        result = orchestrator.scan_skill_sync(sample_skill)

        assert result.skill_name == "test-skill"
        assert result.scan_duration_ms is not None


class TestScoreCalculation:
    def test_perfect_score(self):
        orchestrator = ReadinessOrchestrator()
        score = orchestrator._calculate_score([])
        assert score == 100

    def test_critical_penalty(self):
        orchestrator = ReadinessOrchestrator()
        findings = [
            Finding(
                category=SkillReadinessCategory.METADATA_VALIDATION,
                severity=Severity.CRITICAL,
                title="Test",
                description="Test",
                provider="test",
            )
        ]
        score = orchestrator._calculate_score(findings)
        assert score == 75

    def test_high_penalty(self):
        orchestrator = ReadinessOrchestrator()
        findings = [
            Finding(
                category=SkillReadinessCategory.DESCRIPTION_QUALITY,
                severity=Severity.HIGH,
                title="Test",
                description="Test",
                provider="test",
            )
        ]
        score = orchestrator._calculate_score(findings)
        assert score == 85

    def test_multiple_findings(self):
        orchestrator = ReadinessOrchestrator()
        findings = [
            Finding(
                category=SkillReadinessCategory.DESCRIPTION_QUALITY,
                severity=Severity.HIGH,
                title="High",
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
            Finding(
                category=SkillReadinessCategory.TERMINOLOGY_CONSISTENCY,
                severity=Severity.LOW,
                title="Low",
                description="Test",
                provider="test",
            ),
        ]
        score = orchestrator._calculate_score(findings)
        assert score == 100 - 15 - 8 - 3
        assert score == 74

    def test_score_floor(self):
        orchestrator = ReadinessOrchestrator()
        findings = [
            Finding(
                category=SkillReadinessCategory.METADATA_VALIDATION,
                severity=Severity.CRITICAL,
                title=f"Critical {i}",
                description="Test",
                provider="test",
            )
            for i in range(10)
        ]
        score = orchestrator._calculate_score(findings)
        assert score == 0


class TestGetOrchestrator:
    def test_default_providers(self):
        orchestrator = get_orchestrator()
        assert len(orchestrator.providers) > 0
        provider_names = [p.name for p in orchestrator.providers]
        assert "heuristic" in provider_names

    def test_custom_providers(self):
        providers = [HeuristicProvider()]
        orchestrator = get_orchestrator(providers=providers)
        assert len(orchestrator.providers) == 1
