"""SARIF 2.1.0 report generator for GitHub Code Scanning."""

import json
from datetime import datetime, timezone
from typing import Any

from skillreadiness.core.models import ScanResult, Severity
from skillreadiness.core.taxonomy import CATEGORY_DESCRIPTIONS


def get_sarif_level(severity: Severity) -> str:
    """Convert severity to SARIF level."""
    return {
        Severity.CRITICAL: "error",
        Severity.HIGH: "error",
        Severity.MEDIUM: "warning",
        Severity.LOW: "note",
        Severity.INFO: "none",
    }.get(severity, "warning")


def render_sarif(result: ScanResult) -> str:
    """Render scan result as SARIF 2.1.0 JSON."""
    rules: list[dict[str, Any]] = []
    results_list: list[dict[str, Any]] = []
    seen_rules: set[str] = set()

    for finding in result.findings:
        rule_id = finding.rule_id or f"SRDNS-{hash(finding.title) % 1000:03d}"

        if rule_id not in seen_rules:
            seen_rules.add(rule_id)

            category_desc = CATEGORY_DESCRIPTIONS.get(finding.category, {})
            help_text = category_desc.get("remediation", finding.remediation or "")

            rules.append(
                {
                    "id": rule_id,
                    "name": finding.title,
                    "shortDescription": {"text": finding.title},
                    "fullDescription": {"text": finding.description},
                    "help": {
                        "text": help_text.strip() if help_text else finding.description,
                        "markdown": f"## {finding.title}\n\n{finding.description}\n\n### Remediation\n\n{help_text.strip() if help_text else 'No specific remediation provided.'}",
                    },
                    "defaultConfiguration": {"level": get_sarif_level(finding.severity)},
                    "properties": {
                        "category": str(finding.category),
                        "severity": finding.severity.value,
                    },
                }
            )

        sarif_result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": get_sarif_level(finding.severity),
            "message": {"text": finding.description},
            "properties": {
                "category": str(finding.category),
                "provider": finding.provider,
            },
        }

        if finding.location:
            location_parts = finding.location.split(":")
            file_path = location_parts[0]
            line_num = 1

            if len(location_parts) > 1:
                try:
                    line_num = int(location_parts[1])
                except ValueError:
                    pass

            sarif_result["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": file_path,
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {"startLine": line_num},
                    }
                }
            ]

        if finding.remediation:
            sarif_result["fixes"] = [
                {"description": {"text": finding.remediation}}
            ]

        results_list.append(sarif_result)

    sarif_doc: dict[str, Any] = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "skill-readiness-analyzer",
                        "version": "0.1.0",
                        "informationUri": "https://github.com/nik-kale/skill-readiness-analyzer",
                        "rules": rules,
                    }
                },
                "results": results_list,
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "endTimeUtc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    }
                ],
                "properties": {
                    "skill_name": result.skill_name,
                    "readiness_score": result.readiness_score,
                    "readiness_label": result.readiness_label,
                },
            }
        ],
    }

    return json.dumps(sarif_doc, indent=2)
