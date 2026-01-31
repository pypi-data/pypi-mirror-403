"""Storage layer for database operations and caching.

This package provides the persistence layer for the code index,
using SQLite with WAL mode for concurrent read performance.

Components:
    - Database: Low-level SQLite wrapper with transaction support
    - Repository: High-level data access pattern with query caching
    - ContextPackCache: LRU cache for context packs with disk persistence
    - QueryCache: TTL-based LRU cache for expensive recursive queries

Data Types:
    - Reference: Symbol reference from another location
    - ApiEndpoint: REST API endpoint definition
    - ComponentInfo: Architectural component with statistics
    - ExternalDependency: Third-party dependency information

Utilities:
    - filter_source_files: Filter file lists to source code only

Database Schema (v1.4.0):
    - files: Source files with content hash and component assignment
    - symbols: Functions, classes, methods with FQN and signature
    - edges: Call/import relationships between symbols
    - components: Architectural layer assignments
    - ai_understanding: Cache for AI agent analysis
"""

from civyk_repoix.storage.cache import ContextPackCache
from civyk_repoix.storage.database import Database
from civyk_repoix.storage.repository import (
    ApiEndpoint,
    ComponentInfo,
    ExternalDependency,
    Reference,
    Repository,
    create_repository,
    filter_source_files,
)

__all__ = [
    "ApiEndpoint",
    "ComponentInfo",
    "ContextPackCache",
    "Database",
    "ExternalDependency",
    "filter_source_files",
    "Reference",
    "Repository",
    "create_repository",
]
