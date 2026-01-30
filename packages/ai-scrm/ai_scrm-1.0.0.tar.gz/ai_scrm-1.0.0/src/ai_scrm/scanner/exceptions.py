"""
Scanner exceptions for AI-SCRM.
"""


class ScannerError(Exception):
    """Base exception for scanner operations."""
    pass


class ConfigNotFoundError(ScannerError):
    """Raised when expected configuration file is not found."""
    pass


class MCPConnectionError(ScannerError):
    """Raised when unable to connect to MCP server."""
    pass


class ModelInferenceError(ScannerError):
    """Raised when unable to infer model metadata."""
    pass
