"""Inspection providers for skill readiness analysis."""

from skillreadiness.providers.base import InspectionProvider
from skillreadiness.providers.heuristic_provider import HeuristicProvider

__all__ = [
    "InspectionProvider",
    "HeuristicProvider",
    "get_default_providers",
]


def get_default_providers() -> list[InspectionProvider]:
    """Get the default list of available providers."""
    providers: list[InspectionProvider] = [HeuristicProvider()]
    return providers
