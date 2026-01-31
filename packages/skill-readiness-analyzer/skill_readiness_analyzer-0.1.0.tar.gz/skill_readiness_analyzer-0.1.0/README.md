# Skill Readiness Analyzer

[![PyPI version](https://badge.fury.io/py/skill-readiness-analyzer.svg)](https://badge.fury.io/py/skill-readiness-analyzer)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Production readiness scanner for AI Agent Skills** - Quality gates, best practices compliance, and operational excellence for the Agent Skills ecosystem.

> Beyond security: Ensure your skills are production-ready, efficient, and follow best practices.

![Demo](demo.gif)

## Why Skill Readiness Analyzer?

Security scanning catches malicious code. **Readiness scanning** ensures skills are production-quality:

- **Token Efficiency** - Keep skills under context limits
- **Best Practices** - Follow Anthropic/Cursor guidelines
- **Cross-Platform** - Work on Claude, Cursor, Codex, and more
- **Documentation Quality** - Clear descriptions and triggers
- **Script Reliability** - Error handling in utility scripts

> **Complementary to security scanning**: This tool focuses on operational quality and best practices. For security analysis (prompt injection, data exfiltration, malicious code), use dedicated security scanners.

## Quick Start

### Installation

```bash
pip install skill-readiness-analyzer
```

### Scan a Skill

```bash
# Scan single skill
skill-readiness scan /path/to/my-skill/

# Scan all skills in directory
skill-readiness scan-skills /path/to/skills/

# Output as SARIF for GitHub Code Scanning
skill-readiness scan /path/to/skill --format sarif --output results.sarif
```

### Example Output

```
============================================================
Skill: my-project-skill
============================================================
Readiness Score: 72/100 (NEEDS IMPROVEMENT)

HIGH: SRDNS-005 - Description missing activation context
    → Description lacks "Use when..." clause
    → Location: SKILL.md:description
    → Remediation: Add trigger scenarios to description

MEDIUM: SRDNS-001 - SKILL.md exceeds recommended length
    → SKILL.md has 847 lines (recommended: <500)
    → Location: SKILL.md
    → Remediation: Use progressive disclosure with file references

MEDIUM: SRDNS-003 - No progressive disclosure utilized
    → Large skill with no file references found
    → Remediation: Consider splitting detailed content into reference.md
```

## Readiness Categories

| Category                  | Description                       | Severity |
| ------------------------- | --------------------------------- | -------- |
| `token-footprint`         | SKILL.md exceeds size limits      | MEDIUM   |
| `progressive-disclosure`  | Content not split into references | MEDIUM   |
| `description-quality`     | Missing triggers, wrong person    | HIGH     |
| `platform-compatibility`  | Uses platform-specific features   | MEDIUM   |
| `dependency-completeness` | Missing tool/MCP declarations     | HIGH     |
| `instruction-clarity`     | Ambiguous or conflicting          | MEDIUM   |
| `metadata-validation`     | Invalid frontmatter               | HIGH     |
| `reference-depth`         | Nested references                 | LOW      |
| `terminology-consistency` | Mixed terminology                 | LOW      |
| `script-reliability`      | Scripts lack error handling       | MEDIUM   |

## Heuristic Rules

15 built-in checks based on Anthropic/Cursor best practices:

| Rule      | Check                                |
| --------- | ------------------------------------ |
| SRDNS-001 | SKILL.md exceeds 500 lines           |
| SRDNS-002 | Token count exceeds 2000             |
| SRDNS-003 | No file references for large skills  |
| SRDNS-004 | Large code blocks inline (>50 lines) |
| SRDNS-005 | Description missing "Use when..."    |
| SRDNS-006 | Description uses first/second person |
| SRDNS-007 | Description too short (<50 chars)    |
| SRDNS-008 | Missing required name field          |
| SRDNS-009 | Missing required description field   |
| SRDNS-010 | Invalid name format                  |
| SRDNS-011 | Nested references detected           |
| SRDNS-012 | Mixed terminology                    |
| SRDNS-013 | Conflicting instructions             |
| SRDNS-014 | Python script missing try/except     |
| SRDNS-015 | Shell script missing set -e          |

## Readiness Score

Skills are scored 0-100 based on findings:

| Score  | Label              | Meaning                           |
| ------ | ------------------ | --------------------------------- |
| 90-100 | Production Ready   | Ship it!                          |
| 70-89  | Needs Improvement  | Fix high-severity issues          |
| 50-69  | Significant Issues | Major rework needed               |
| 0-49   | Not Ready          | Start over or fix critical issues |

**Penalties:**

- CRITICAL: -25 points
- HIGH: -15 points
- MEDIUM: -8 points
- LOW: -3 points

## CI/CD Integration

### GitHub Actions

```yaml
name: Skill Readiness

on: [push, pull_request]

jobs:
  readiness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install skill-readiness-analyzer
        run: pip install skill-readiness-analyzer

      - name: Scan skills
        run: |
          skill-readiness scan .cursor/skills/my-skill \
            --format sarif \
            --output results.sarif \
            --fail-on high

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

### Using the Action

```yaml
- uses: nik-kale/skill-readiness-analyzer@v1
  with:
    path: .cursor/skills/my-skill
    fail-on: high
```

## Output Formats

### Summary (default)

Human-readable console output with colors and emojis.

### JSON

```bash
skill-readiness scan /path/to/skill --format json
```

### Markdown

```bash
skill-readiness scan /path/to/skill --format markdown
```

### SARIF

For GitHub Code Scanning integration:

```bash
skill-readiness scan /path/to/skill --format sarif --output results.sarif
```

## CLI Reference

```bash
# Scan single skill
skill-readiness scan PATH [OPTIONS]
  --format, -f [summary|json|markdown|sarif]
  --output, -o FILE
  --verbose, -v
  --fail-on [critical|high|medium|low]

# Scan multiple skills
skill-readiness scan-skills PATH [OPTIONS]
  --glob, -g PATTERN    # Default: */SKILL.md
  --format, -f [summary|json|markdown]
  --output, -o FILE
  --verbose, -v

# List categories
skill-readiness list-categories

# List providers
skill-readiness list-providers

# Generate config file
skill-readiness init [--format toml|yaml]
```

## Configuration

Create `.skill-readiness.toml`:

```toml
[scan]
timeout_seconds = 30.0

[output]
format = "summary"
verbose = false

[heuristic]
max_lines = 500
max_tokens = 2000
min_description_length = 50

[fail]
severity = "high"
```

## Programmatic Usage

```python
from skillreadiness.core.orchestrator import get_orchestrator
from skillreadiness.reports import render_markdown

orchestrator = get_orchestrator()
result = orchestrator.scan_skill_sync("/path/to/skill")

print(f"Score: {result.readiness_score}/100")
print(f"Status: {result.readiness_label}")

for finding in result.findings:
    print(f"[{finding.severity.value}] {finding.title}")

report = render_markdown(result, verbose=True)
print(report)
```

## Best Practices Reference

This tool implements checks based on:

1. **Anthropic's Agent Skills Guidelines** - Progressive disclosure, token efficiency
2. **Cursor's create-skill SKILL.md** - Description quality, metadata validation
3. **Agent Skills Specification** - Schema validation, compatibility

Key best practices enforced:

- Keep SKILL.md under 500 lines
- Write descriptions in third person
- Include "Use when..." activation context
- Use file references for detailed content
- Add error handling to scripts
- Declare all dependencies

## Contributing

Contributions welcome! Areas of interest:

- Additional heuristic rules
- Platform compatibility checks
- YARA rules for pattern detection
- LLM-based semantic analysis

## License

MIT License - see [LICENSE](LICENSE) for details.

## Ecosystem

This tool is part of a broader quality ecosystem for AI agents:

| Tool                                                                       | Focus                   | Use Case                                  |
| -------------------------------------------------------------------------- | ----------------------- | ----------------------------------------- |
| **skill-readiness-analyzer**                                               | Operational quality     | Best practices, efficiency, compatibility |
| [mcp-readiness-scanner](https://github.com/nik-kale/mcp-readiness-scanner) | MCP operational quality | Production readiness for MCP tools        |

For security-focused analysis of Agent Skills and MCP servers, the community has developed dedicated security scanning tools.
