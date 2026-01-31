"""JSON report generator."""

import json
from typing import Any

from skillreadiness.core.models import ScanResult


def render_json(result: ScanResult, indent: int | None = 2) -> str:
    """Render scan result as JSON."""
    return result.model_dump_json(indent=indent)


def render_json_summary(result: ScanResult) -> str:
    """Render a summary JSON with key metrics only."""
    summary: dict[str, Any] = {
        "skill_name": result.skill_name,
        "readiness_score": result.readiness_score,
        "readiness_label": result.readiness_label,
        "is_production_ready": result.is_production_ready,
        "finding_counts": result.finding_counts_by_severity,
        "total_findings": len(result.findings),
        "providers_used": result.providers_used,
        "scan_duration_ms": result.scan_duration_ms,
    }
    return json.dumps(summary, indent=2)
