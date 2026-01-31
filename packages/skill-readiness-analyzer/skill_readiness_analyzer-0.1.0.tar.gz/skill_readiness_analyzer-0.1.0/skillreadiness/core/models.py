"""Core data models for skill readiness analysis."""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, computed_field


class Severity(str, Enum):
    """Severity levels for findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SkillReadinessCategory(str, Enum):
    """Operational risk categories for skill readiness."""

    TOKEN_FOOTPRINT = "token-footprint"
    PROGRESSIVE_DISCLOSURE = "progressive-disclosure"
    DESCRIPTION_QUALITY = "description-quality"
    PLATFORM_COMPATIBILITY = "platform-compatibility"
    DEPENDENCY_COMPLETENESS = "dependency-completeness"
    INSTRUCTION_CLARITY = "instruction-clarity"
    METADATA_VALIDATION = "metadata-validation"
    REFERENCE_DEPTH = "reference-depth"
    TERMINOLOGY_CONSISTENCY = "terminology-consistency"
    SCRIPT_RELIABILITY = "script-reliability"


class SkillManifest(BaseModel):
    """Parsed frontmatter from SKILL.md."""

    name: str | None = None
    description: str | None = None
    license: str | None = None
    compatibility: str | None = None
    allowed_tools: list[str] | None = None
    metadata: dict[str, Any] | None = None
    disable_model_invocation: bool = False


class SkillFile(BaseModel):
    """A file within a skill package."""

    path: Path
    relative_path: str
    file_type: str
    content: str | None = None
    size_bytes: int = 0


class Skill(BaseModel):
    """A parsed skill package."""

    directory: Path
    manifest: SkillManifest
    skill_md_path: Path
    instruction_body: str
    files: list[SkillFile] = Field(default_factory=list)
    referenced_files: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def name(self) -> str:
        """Get the skill name from manifest or directory."""
        if self.manifest.name:
            return self.manifest.name
        return self.directory.name


class Finding(BaseModel):
    """A readiness finding from analysis."""

    category: SkillReadinessCategory
    severity: Severity
    title: str
    description: str
    location: str | None = None
    evidence: dict[str, Any] | None = None
    provider: str
    remediation: str | None = None
    rule_id: str | None = None


class ScanResult(BaseModel):
    """Result of scanning a single skill."""

    skill_name: str
    skill_directory: str
    findings: list[Finding] = Field(default_factory=list)
    suppressed_findings: list[Finding] | None = None
    readiness_score: int = 100
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    providers_used: list[str] = Field(default_factory=list)
    scan_duration_ms: int | None = None
    metadata: dict[str, Any] | None = None

    @computed_field
    @property
    def has_critical_findings(self) -> bool:
        """Check if any critical findings exist."""
        return any(f.severity == Severity.CRITICAL for f in self.findings)

    @computed_field
    @property
    def has_high_findings(self) -> bool:
        """Check if any high severity findings exist."""
        return any(f.severity == Severity.HIGH for f in self.findings)

    @computed_field
    @property
    def is_production_ready(self) -> bool:
        """Check if skill is considered production ready (score >= 90)."""
        return self.readiness_score >= 90

    @computed_field
    @property
    def readiness_label(self) -> str:
        """Get human-readable readiness label."""
        if self.readiness_score >= 90:
            return "Production Ready"
        elif self.readiness_score >= 70:
            return "Needs Improvement"
        elif self.readiness_score >= 50:
            return "Significant Issues"
        else:
            return "Not Ready"

    @computed_field
    @property
    def finding_counts_by_severity(self) -> dict[str, int]:
        """Get counts of findings by severity."""
        counts: dict[str, int] = {s.value: 0 for s in Severity}
        for finding in self.findings:
            counts[finding.severity.value] += 1
        return counts


class MultiScanResult(BaseModel):
    """Result of scanning multiple skills."""

    scan_results: list[ScanResult] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_scan_duration_ms: int | None = None

    @computed_field
    @property
    def total_skills_scanned(self) -> int:
        """Total number of skills scanned."""
        return len(self.scan_results)

    @computed_field
    @property
    def total_findings(self) -> int:
        """Total number of findings across all skills."""
        return sum(len(r.findings) for r in self.scan_results)

    @computed_field
    @property
    def average_readiness_score(self) -> float:
        """Average readiness score across all skills."""
        if not self.scan_results:
            return 0.0
        return sum(r.readiness_score for r in self.scan_results) / len(self.scan_results)

    @computed_field
    @property
    def skills_production_ready(self) -> int:
        """Number of skills that are production ready."""
        return sum(1 for r in self.scan_results if r.is_production_ready)
