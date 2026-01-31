"""Markdown report generator."""

from skillreadiness.core.models import ScanResult, Severity


def get_severity_emoji(severity: Severity) -> str:
    """Get emoji for severity level."""
    return {
        Severity.CRITICAL: "🔴",
        Severity.HIGH: "🟠",
        Severity.MEDIUM: "🟡",
        Severity.LOW: "🔵",
        Severity.INFO: "⚪",
    }.get(severity, "⚪")


def get_readiness_emoji(score: int) -> str:
    """Get emoji for readiness score."""
    if score >= 90:
        return "✅"
    elif score >= 70:
        return "⚠️"
    elif score >= 50:
        return "⛔"
    else:
        return "🚫"


def render_markdown(result: ScanResult, verbose: bool = False) -> str:
    """Render scan result as Markdown."""
    lines: list[str] = []

    emoji = get_readiness_emoji(result.readiness_score)
    lines.append(f"## {emoji} {result.skill_name}")
    lines.append("")
    lines.append(f"**Readiness Score:** {result.readiness_score}/100 ({result.readiness_label})")
    lines.append(f"**Directory:** `{result.skill_directory}`")
    lines.append(f"**Providers:** {', '.join(result.providers_used)}")

    if result.scan_duration_ms:
        lines.append(f"**Scan Duration:** {result.scan_duration_ms}ms")

    lines.append("")

    if not result.findings:
        lines.append("No issues found! ✅")
        return "\n".join(lines)

    lines.append("### Findings")
    lines.append("")
    lines.append("| Severity | Rule | Title | Location |")
    lines.append("|----------|------|-------|----------|")

    for finding in sorted(result.findings, key=lambda f: f.severity.value):
        emoji = get_severity_emoji(finding.severity)
        severity = f"{emoji} {finding.severity.value.upper()}"
        rule = finding.rule_id or "N/A"
        title = finding.title
        location = f"`{finding.location}`" if finding.location else "—"
        lines.append(f"| {severity} | {rule} | {title} | {location} |")

    if verbose:
        lines.append("")
        lines.append("### Details")
        lines.append("")

        for finding in sorted(result.findings, key=lambda f: f.severity.value):
            emoji = get_severity_emoji(finding.severity)
            lines.append(f"#### {emoji} {finding.rule_id}: {finding.title}")
            lines.append("")
            lines.append(f"**Severity:** {finding.severity.value.upper()}")
            lines.append(f"**Category:** {finding.category}")

            if finding.location:
                lines.append(f"**Location:** `{finding.location}`")

            lines.append("")
            lines.append(finding.description)
            lines.append("")

            if finding.remediation:
                lines.append(f"**Remediation:** {finding.remediation}")
                lines.append("")

            if finding.evidence:
                lines.append("<details>")
                lines.append("<summary>Evidence</summary>")
                lines.append("")
                lines.append("```json")
                import json

                lines.append(json.dumps(finding.evidence, indent=2))
                lines.append("```")
                lines.append("</details>")
                lines.append("")

    return "\n".join(lines)


def render_pr_comment(result: ScanResult) -> str:
    """Render a concise PR comment format."""
    lines: list[str] = []

    emoji = get_readiness_emoji(result.readiness_score)
    lines.append(f"### {emoji} Skill Readiness: {result.skill_name}")
    lines.append("")
    lines.append(f"**Score:** {result.readiness_score}/100 ({result.readiness_label})")
    lines.append("")

    counts = result.finding_counts_by_severity
    badges = []
    if counts.get("critical", 0):
        badges.append(f"🔴 {counts['critical']} Critical")
    if counts.get("high", 0):
        badges.append(f"🟠 {counts['high']} High")
    if counts.get("medium", 0):
        badges.append(f"🟡 {counts['medium']} Medium")
    if counts.get("low", 0):
        badges.append(f"🔵 {counts['low']} Low")

    if badges:
        lines.append(" | ".join(badges))
    else:
        lines.append("No issues found! ✅")

    return "\n".join(lines)
