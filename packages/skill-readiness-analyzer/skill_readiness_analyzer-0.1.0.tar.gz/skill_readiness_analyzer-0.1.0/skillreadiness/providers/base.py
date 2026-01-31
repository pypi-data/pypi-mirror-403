"""Base class for inspection providers."""

from abc import ABC, abstractmethod

from skillreadiness.core.models import Finding, Skill


class InspectionProvider(ABC):
    """Abstract base class for skill inspection providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for identification."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of the provider."""
        return f"{self.name} provider"

    @abstractmethod
    async def analyze(self, skill: Skill) -> list[Finding]:
        """Analyze a skill and return findings.

        Args:
            skill: The parsed skill to analyze.

        Returns:
            List of findings from analysis.
        """
        ...

    def is_available(self) -> bool:
        """Check if the provider is available (dependencies installed)."""
        return True

    def get_unavailable_reason(self) -> str | None:
        """Get reason why provider is unavailable, if applicable."""
        if self.is_available():
            return None
        return "Provider dependencies not installed"

    async def initialize(self) -> None:
        """Initialize provider resources. Called before analysis."""
        pass

    async def cleanup(self) -> None:
        """Clean up provider resources. Called after analysis."""
        pass
