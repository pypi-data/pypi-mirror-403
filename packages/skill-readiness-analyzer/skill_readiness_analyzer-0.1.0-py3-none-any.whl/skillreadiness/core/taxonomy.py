"""Skill Readiness Taxonomy - Category definitions and remediation guidance.

This module provides detailed descriptions for each operational readiness
category. These categories focus on production quality and best practices,
NOT security vulnerabilities (see skill-scanner for security analysis).
"""

from typing import Any

from skillreadiness.core.models import Severity, SkillReadinessCategory

__all__ = [
    "CATEGORY_DESCRIPTIONS",
    "get_category_description",
    "get_category_severity",
    "format_category_help",
    "format_taxonomy_overview",
]

CATEGORY_DESCRIPTIONS: dict[SkillReadinessCategory, dict[str, Any]] = {
    SkillReadinessCategory.TOKEN_FOOTPRINT: {
        "name": "Token Footprint",
        "short_description": "SKILL.md exceeds recommended size limits for efficient context usage",
        "long_description": """
Skills consume context window space shared with conversation history,
other skills, and the current request. Oversized skills reduce available
context for actual work.

Risk factors:
- SKILL.md exceeding 500 lines
- Estimated token count over 2000
- Large inline code blocks
- Verbose explanations that don't add value

Impact:
- Reduced context for conversation history
- Higher API costs per interaction
- Slower response times
- Potential truncation of important content
""",
        "default_severity": Severity.MEDIUM,
        "remediation": """
1. Keep SKILL.md under 500 lines
2. Use progressive disclosure - put details in referenced files
3. Assume the agent is already smart - only add unique knowledge
4. Challenge each paragraph: "Does this justify its token cost?"
5. Use scripts instead of inline code where possible
""",
    },
    SkillReadinessCategory.PROGRESSIVE_DISCLOSURE: {
        "name": "Progressive Disclosure",
        "short_description": "Detailed content embedded instead of progressively loaded via references",
        "long_description": """
Progressive disclosure is an Anthropic-recommended pattern where essential
information lives in SKILL.md while detailed reference material lives in
separate files that are read only when needed.

Symptoms of poor progressive disclosure:
- Large code blocks inline (>50 lines)
- Detailed API documentation embedded
- Complete examples instead of representative snippets
- No file references in the skill

Benefits of proper progressive disclosure:
- Reduced base token cost
- Faster initial skill loading
- Better context utilization
- More responsive agent behavior
""",
        "default_severity": Severity.MEDIUM,
        "remediation": """
1. Put essential quick-start information in SKILL.md
2. Create reference.md for detailed documentation
3. Create examples.md for comprehensive examples
4. Use markdown links: [see reference.md](reference.md)
5. Keep references one level deep - avoid nested reference chains
""",
    },
    SkillReadinessCategory.DESCRIPTION_QUALITY: {
        "name": "Description Quality",
        "short_description": "Description lacks clarity, trigger terms, or activation context",
        "long_description": """
The description field is critical for skill discovery. The agent uses it
to decide when to apply the skill. Poor descriptions lead to skills being
applied at wrong times or not applied when they should be.

Quality issues:
- Missing "Use when..." clause (activation context)
- Written in first or second person instead of third person
- Too vague or generic (under 50 characters)
- Missing trigger terms that match user intent

Impact:
- Skills applied at inappropriate times
- Skills not discovered when they should be
- Agent confusion about skill purpose
- Poor user experience
""",
        "default_severity": Severity.HIGH,
        "remediation": """
1. Write in third person: "Processes Excel files" not "I can process"
2. Include WHAT the skill does and WHEN to use it
3. Add specific trigger terms users might say
4. Example: "Extract text from PDF files, fill forms, merge documents.
   Use when working with PDF files or when the user mentions PDFs."
5. Aim for 100-300 characters with clear, specific language
""",
    },
    SkillReadinessCategory.PLATFORM_COMPATIBILITY: {
        "name": "Platform Compatibility",
        "short_description": "Uses features unavailable across all agent platforms",
        "long_description": """
Agent skills may run on different platforms (Claude Code, Cursor, VS Code,
Copilot, Codex) with varying feature availability. Skills using platform-
specific features may fail or behave unexpectedly on other platforms.

Compatibility concerns:
- Bash/shell tool access (not available everywhere)
- Filesystem write access (restricted on some platforms)
- Browser tools (not universally available)
- MCP server dependencies
- Platform-specific tool names

Impact:
- Skills fail silently on incompatible platforms
- Reduced skill portability
- Maintenance burden for multi-platform support
- User confusion when skills don't work
""",
        "default_severity": Severity.MEDIUM,
        "remediation": """
1. Document required platform features
2. Provide fallback instructions for restricted environments
3. Test skills on target platforms before deployment
4. Use conditional workflows based on available tools
5. Prefer cross-platform solutions where possible
""",
    },
    SkillReadinessCategory.DEPENDENCY_COMPLETENESS: {
        "name": "Dependency Completeness",
        "short_description": "References tools, MCP servers, or resources not declared in metadata",
        "long_description": """
Skills that reference external dependencies without declaring them will
fail at runtime when those dependencies aren't available. This includes
MCP servers, specific tools, Python packages, or external services.

Missing dependency patterns:
- MCP server references without availability check
- Tool references not in allowed-tools list
- Python imports in scripts without package declaration
- External API calls without documentation

Impact:
- Runtime failures on fresh installations
- Confusing error messages
- Skills that work locally but fail in CI/CD
- Maintenance burden tracking hidden dependencies
""",
        "default_severity": Severity.HIGH,
        "remediation": """
1. List all required tools in allowed-tools field
2. Document required MCP servers and their purpose
3. Include requirements.txt or pyproject.toml for Python deps
4. Add dependency check instructions at skill start
5. Provide clear error messages for missing dependencies
""",
    },
    SkillReadinessCategory.INSTRUCTION_CLARITY: {
        "name": "Instruction Clarity",
        "short_description": "Instructions are ambiguous, conflicting, or unclear",
        "long_description": """
Clear instructions are essential for consistent skill execution. Ambiguous
or conflicting instructions lead to unpredictable agent behavior and
inconsistent results.

Clarity issues:
- Multiple options without clear default
- Conflicting guidance in different sections
- Vague language ("might", "could", "sometimes")
- Missing decision criteria for workflows

Impact:
- Inconsistent skill execution
- Agent confusion and poor decisions
- User frustration with unpredictable results
- Difficulty debugging skill behavior
""",
        "default_severity": Severity.MEDIUM,
        "remediation": """
1. Provide clear defaults with escape hatches
2. Use definitive language: "Use X" not "You could use X"
3. Review for conflicting instructions
4. Add decision criteria for conditional workflows
5. Include concrete examples for ambiguous cases
""",
    },
    SkillReadinessCategory.METADATA_VALIDATION: {
        "name": "Metadata Validation",
        "short_description": "Missing or invalid frontmatter fields in SKILL.md",
        "long_description": """
Valid metadata in SKILL.md frontmatter is required for proper skill
registration and discovery. Invalid or missing metadata prevents skills
from being loaded or causes registration errors.

Validation requirements:
- name: required, max 64 chars, lowercase letters/numbers/hyphens
- description: required, max 1024 chars, non-empty
- Other fields have specific format requirements

Impact:
- Skills fail to register
- Discovery doesn't work correctly
- Ecosystem tooling breaks
- Silent failures in skill loading
""",
        "default_severity": Severity.HIGH,
        "remediation": """
1. Ensure name field exists and follows format rules
2. Ensure description field exists and is non-empty
3. Validate against skill specification schema
4. Use consistent field naming (kebab-case or snake_case)
5. Test skill loading before deployment
""",
    },
    SkillReadinessCategory.REFERENCE_DEPTH: {
        "name": "Reference Depth",
        "short_description": "Nested references beyond recommended one level",
        "long_description": """
Deep reference chains (references that reference other references) can
cause partial reads and confusion. Best practice is to keep references
one level deep from SKILL.md.

Problems with deep references:
- Agent may not follow the full chain
- Increases token cost when traversing
- Creates maintenance complexity
- May cause circular reference issues

Recommended structure:
- SKILL.md -> reference.md (good)
- SKILL.md -> reference.md -> details.md (problematic)
""",
        "default_severity": Severity.LOW,
        "remediation": """
1. Link directly from SKILL.md to reference files
2. Consolidate deeply nested content
3. Use flat reference structure
4. Avoid circular references
5. Merge small referenced files into parent
""",
    },
    SkillReadinessCategory.TERMINOLOGY_CONSISTENCY: {
        "name": "Terminology Consistency",
        "short_description": "Inconsistent naming or terminology throughout the skill",
        "long_description": """
Consistent terminology helps agents and users understand skills clearly.
Mixed terminology creates confusion and can lead to misinterpretation.

Inconsistency examples:
- Mixing "API endpoint", "URL", "route", "path" for same concept
- Mixing "field", "box", "element", "control" for form fields
- Inconsistent casing (camelCase vs snake_case)
- Abbreviated and full terms interchangeably

Impact:
- Agent confusion about concepts
- Difficulty following instructions
- Maintenance burden
- Poor user experience
""",
        "default_severity": Severity.LOW,
        "remediation": """
1. Choose one term for each concept and use it consistently
2. Define terminology at the start if needed
3. Use consistent casing throughout
4. Review skill for mixed terminology
5. Create a glossary for complex domains
""",
    },
    SkillReadinessCategory.SCRIPT_RELIABILITY: {
        "name": "Script Reliability",
        "short_description": "Scripts lack error handling, dependency declarations, or safety features",
        "long_description": """
Utility scripts in skills should be production-ready with proper error
handling and safety features. Unreliable scripts cause runtime failures
and poor user experience.

Reliability issues:
- Python scripts without try/except blocks
- Shell scripts without set -e (fail on error)
- Missing dependency declarations
- No input validation
- Missing output format documentation

Impact:
- Silent failures during execution
- Confusing error messages
- Difficult debugging
- Inconsistent behavior
""",
        "default_severity": Severity.MEDIUM,
        "remediation": """
1. Add try/except blocks to Python scripts
2. Use set -e at start of shell scripts
3. Document required dependencies
4. Validate inputs before processing
5. Provide clear success/failure output
""",
    },
}


def get_category_description(category: SkillReadinessCategory) -> dict[str, Any]:
    """Get the full description for an operational risk category."""
    return CATEGORY_DESCRIPTIONS.get(category, {})


def get_category_severity(category: SkillReadinessCategory) -> Severity:
    """Get the default severity for a category."""
    desc = CATEGORY_DESCRIPTIONS.get(category, {})
    return desc.get("default_severity", Severity.MEDIUM)


def format_category_help(category: SkillReadinessCategory) -> str:
    """Format a category's information for display."""
    desc = CATEGORY_DESCRIPTIONS.get(category, {})
    if not desc:
        return f"Unknown category: {category.value}"

    lines = [
        f"## {desc['name']}",
        "",
        f"**Category ID:** `{category.value}`",
        f"**Default Severity:** {desc['default_severity'].value}",
        "",
        "### Description",
        desc["short_description"],
        "",
        desc["long_description"].strip(),
        "",
        "### Remediation",
        desc["remediation"].strip(),
    ]
    return "\n".join(lines)


def format_taxonomy_overview() -> str:
    """Format the complete taxonomy for documentation."""
    lines = [
        "# Skill Readiness Analyzer - Operational Risk Taxonomy",
        "",
        "This taxonomy covers operational readiness risks for Agent Skills.",
        "For security vulnerabilities, see Cisco's skill-scanner.",
        "",
    ]

    for category in SkillReadinessCategory:
        lines.append(format_category_help(category))
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
