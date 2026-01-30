"""
AI-SCRM Framework Integrations.

Provides one-liner integrations for common frameworks.

Example:
    >>> from ai_scrm.integrations import guard, langchain_guard
    >>> 
    >>> @guard(tool="web-search")
    ... def search_web(query):
    ...     return results
"""

from .integrations import (
    guard,
    langchain_guard,
    FastAPIMiddleware,
    EmergencyBypass,
    emergency_bypass,
    is_bypass_active,
    get_bypass_reason,
    SecurityError,
)

__all__ = [
    "guard",
    "langchain_guard",
    "FastAPIMiddleware",
    "EmergencyBypass",
    "emergency_bypass",
    "is_bypass_active",
    "get_bypass_reason",
    "SecurityError",
]
