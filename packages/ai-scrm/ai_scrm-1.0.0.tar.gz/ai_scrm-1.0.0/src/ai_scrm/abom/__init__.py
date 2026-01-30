"""
AI-SCRM Control Domain 1: ABOM - AI Bill of Materials & Provenance

AI-SCS Section 5 Implementation.

Every AI system MUST generate, maintain, and make available an ABOM
describing all AI Supply Chain Assets required for its operation.

Classes:
    ABOM - Root ABOM document (CycloneDX 1.6 aligned)
    ABOMBuilder - Builder for creating ABOMs
    ABOMComponent - Individual component in ABOM
    Hash - Cryptographic hash
    Property - Key-value metadata

Asset Categories (AI-SCS 4.1):
    - Models (base, fine-tuned, adapters)
    - Data (training, fine-tuning, evaluation)
    - Embeddings (models, vector stores)
    - Dependencies (frameworks, tokenizers, inference engines)
    - Agents (planners, orchestrators)
    - Tools (plugins, MCP servers, APIs)
    - Infrastructure (TEEs, accelerators)

Usage:
    from ai_scrm.abom import ABOM, ABOMBuilder
    
    builder = ABOMBuilder()
    builder.add_model(name="llama", version="7b", hash_value="abc...")
    abom = builder.finalize(system_name="my-agent")
    abom.to_file("abom.json")
"""

from ai_scrm.abom.models import (
    ABOM,
    ABOMComponent,
    ABOMDependency,
    ABOMMetadata,
    Hash,
    Property,
    ExternalReference,
    ComponentType,
    ArtifactType,
    AISystemType,
    AIRuntimeType,
)
from ai_scrm.abom.builder import ABOMBuilder
from ai_scrm.abom.exceptions import (
    ABOMError,
    ABOMValidationError,
    ABOMParseError,
)

__all__ = [
    # Core classes
    "ABOM",
    "ABOMComponent",
    "ABOMDependency",
    "ABOMMetadata",
    "Hash",
    "Property",
    "ExternalReference",
    # Builder
    "ABOMBuilder",
    # Enums
    "ComponentType",
    "ArtifactType",
    "AISystemType",
    "AIRuntimeType",
    # Exceptions
    "ABOMError",
    "ABOMValidationError",
    "ABOMParseError",
]
