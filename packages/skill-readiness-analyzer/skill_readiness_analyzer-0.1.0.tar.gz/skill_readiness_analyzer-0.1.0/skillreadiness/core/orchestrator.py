"""Orchestrator for coordinating skill readiness scans."""

import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path

from skillreadiness.core.loader import SkillLoader, SkillLoadError
from skillreadiness.core.models import (
    Finding,
    MultiScanResult,
    ScanResult,
    Severity,
    Skill,
)
from skillreadiness.providers.base import InspectionProvider


class ReadinessOrchestrator:
    """Coordinates skill readiness scanning across multiple providers."""

    SEVERITY_PENALTY = {
        Severity.CRITICAL: 25,
        Severity.HIGH: 15,
        Severity.MEDIUM: 8,
        Severity.LOW: 3,
        Severity.INFO: 0,
    }

    def __init__(
        self,
        providers: list[InspectionProvider] | None = None,
        timeout_seconds: float = 30.0,
    ):
        self.providers = providers or []
        self.timeout_seconds = timeout_seconds
        self.loader = SkillLoader()

    def add_provider(self, provider: InspectionProvider) -> None:
        """Add a provider to the orchestrator."""
        self.providers.append(provider)

    async def scan_skill(self, skill_path: str | Path) -> ScanResult:
        """Scan a single skill and return results."""
        start_time = time.time()
        skill_path = Path(skill_path)

        try:
            skill = self.loader.load_skill(skill_path)
        except SkillLoadError as e:
            return ScanResult(
                skill_name=skill_path.name,
                skill_directory=str(skill_path),
                findings=[
                    Finding(
                        category="metadata-validation",
                        severity=Severity.CRITICAL,
                        title="Failed to load skill",
                        description=str(e),
                        location=str(skill_path),
                        evidence={"error": str(e)},
                        provider="orchestrator",
                        remediation="Ensure SKILL.md exists with valid frontmatter",
                        rule_id="LOAD-ERROR",
                    )
                ],
                readiness_score=0,
                providers_used=["orchestrator"],
                scan_duration_ms=int((time.time() - start_time) * 1000),
            )

        all_findings: list[Finding] = []
        providers_used: list[str] = []

        for provider in self.providers:
            if not provider.is_available():
                continue

            try:
                await provider.initialize()
                findings = await asyncio.wait_for(
                    provider.analyze(skill),
                    timeout=self.timeout_seconds,
                )
                all_findings.extend(findings)
                providers_used.append(provider.name)
            except asyncio.TimeoutError:
                all_findings.append(
                    Finding(
                        category="metadata-validation",
                        severity=Severity.INFO,
                        title=f"Provider timeout: {provider.name}",
                        description=f"Provider {provider.name} exceeded timeout",
                        location=None,
                        evidence={"timeout_seconds": self.timeout_seconds},
                        provider="orchestrator",
                        remediation=None,
                        rule_id="TIMEOUT",
                    )
                )
            except Exception as e:
                all_findings.append(
                    Finding(
                        category="metadata-validation",
                        severity=Severity.INFO,
                        title=f"Provider error: {provider.name}",
                        description=str(e),
                        location=None,
                        evidence={"error": str(e)},
                        provider="orchestrator",
                        remediation=None,
                        rule_id="PROVIDER-ERROR",
                    )
                )
            finally:
                try:
                    await provider.cleanup()
                except Exception:
                    pass

        readiness_score = self._calculate_score(all_findings)
        duration_ms = int((time.time() - start_time) * 1000)

        return ScanResult(
            skill_name=skill.name,
            skill_directory=str(skill_path),
            findings=all_findings,
            readiness_score=readiness_score,
            timestamp=datetime.now(timezone.utc),
            providers_used=providers_used,
            scan_duration_ms=duration_ms,
        )

    async def scan_skills(self, skills_dir: str | Path, glob_pattern: str = "*/SKILL.md") -> MultiScanResult:
        """Scan multiple skills in a directory."""
        start_time = time.time()
        skills_dir = Path(skills_dir)

        skill_dirs: list[Path] = []
        for skill_md in skills_dir.glob(glob_pattern):
            skill_dirs.append(skill_md.parent)

        results: list[ScanResult] = []
        for skill_dir in skill_dirs:
            result = await self.scan_skill(skill_dir)
            results.append(result)

        duration_ms = int((time.time() - start_time) * 1000)

        return MultiScanResult(
            scan_results=results,
            timestamp=datetime.now(timezone.utc),
            total_scan_duration_ms=duration_ms,
        )

    def _calculate_score(self, findings: list[Finding]) -> int:
        """Calculate readiness score based on findings."""
        score = 100

        for finding in findings:
            penalty = self.SEVERITY_PENALTY.get(finding.severity, 0)
            score -= penalty

        return max(0, score)

    def scan_skill_sync(self, skill_path: str | Path) -> ScanResult:
        """Synchronous wrapper for scan_skill."""
        return asyncio.run(self.scan_skill(skill_path))

    def scan_skills_sync(self, skills_dir: str | Path, glob_pattern: str = "*/SKILL.md") -> MultiScanResult:
        """Synchronous wrapper for scan_skills."""
        return asyncio.run(self.scan_skills(skills_dir, glob_pattern))


def get_orchestrator(providers: list[InspectionProvider] | None = None) -> ReadinessOrchestrator:
    """Get an orchestrator with default providers if none specified."""
    from skillreadiness.providers import get_default_providers

    if providers is None:
        providers = get_default_providers()
    return ReadinessOrchestrator(providers=providers)
