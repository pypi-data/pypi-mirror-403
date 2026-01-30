"""
AI-SCRM: AI Supply Chain Risk Management

Quick Start:
    >>> from ai_scrm import Scanner, Monitor
    >>> scanner = Scanner()
    >>> result = scanner.scan()
    >>> monitor = Monitor(abom_path="abom-signed.json")
    >>> monitor.start()

CLI:
    $ ai-scrm init
    $ ai-scrm status
    $ ai-scrm monitor
"""

__version__ = "1.0.0"

from .abom import ABOM, ABOMBuilder, ABOMComponent, ABOMMetadata, Hash, Property
from .trust import Signer, Verifier, TrustAssertion, TrustAssertionBuilder
from .validation import (
    DriftDetector, RADEEmitter, RADEEvent, DriftEvent, 
    ViolationEvent, AttestationEvent, Observation, PolicyEngine, EnforcementAction
)
from .scanner import (
    Scanner, ScanResult, DiscoveredModel, DiscoveredMCP, DiscoveredLibrary,
    MCPDiscovery, TrustBoundaryClassifier, MetadataEnricher, generate_template
)
from .monitor import Monitor, MonitorConfig, MonitorStatus, MonitorState
from .integrations import guard, langchain_guard, FastAPIMiddleware, emergency_bypass, SecurityError

__all__ = [
    "__version__",
    "ABOM", "ABOMBuilder", "ABOMComponent", "ABOMMetadata", "Hash", "Property",
    "Signer", "Verifier", "TrustAssertion", "TrustAssertionBuilder",
    "DriftDetector", "RADEEmitter", "RADEEvent", "DriftEvent", "ViolationEvent",
    "AttestationEvent", "Observation", "PolicyEngine", "EnforcementAction",
    "Scanner", "ScanResult", "DiscoveredModel", "DiscoveredMCP", "DiscoveredLibrary",
    "MCPDiscovery", "TrustBoundaryClassifier", "MetadataEnricher", "generate_template",
    "Monitor", "MonitorConfig", "MonitorStatus", "MonitorState",
    "guard", "langchain_guard", "FastAPIMiddleware", "emergency_bypass", "SecurityError",
]
