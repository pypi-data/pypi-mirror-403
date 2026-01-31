"""Data models for the indexing service.

This package defines the domain entities used throughout the codebase index.
All models are immutable dataclasses with validation and database serialization.

Core Entities:
    Symbol: Code element (class, function, method, variable)
    File: Source file with language and content hash
    Edge: Relationship between symbols (calls, imports, extends)
    Component: Architectural layer assignment

Supporting Entities:
    Manifest: Index metadata with git commit info
    AIUnderstanding: Cached AI analysis of code
    HealthStatus: Service health based on error rates

Type Aliases:
    SymbolKind: Valid symbol types (class, function, method, etc.)
    EdgeKind: Valid edge types (imports, calls, extends, etc.)
    Language: Supported programming languages
    Layer: Architectural layers (presentation, domain, etc.)
    AIUnderstandingScope: Understanding granularity levels
"""

from civyk_repoix.models.ai_understanding import (
    AIUnderstanding,
    AIUnderstandingScope,
    ImportanceLevel,
)
from civyk_repoix.models.component import Component, Layer
from civyk_repoix.models.edge import Edge, EdgeKind
from civyk_repoix.models.file import File, Language
from civyk_repoix.models.manifest import Manifest
from civyk_repoix.models.status import HealthStatus, calculate_health_status
from civyk_repoix.models.symbol import Symbol, SymbolKind

__all__ = [
    "AIUnderstanding",
    "AIUnderstandingScope",
    "Component",
    "Edge",
    "EdgeKind",
    "File",
    "HealthStatus",
    "ImportanceLevel",
    "Language",
    "Layer",
    "Manifest",
    "Symbol",
    "SymbolKind",
    "calculate_health_status",
]
