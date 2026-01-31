"""Background workers for indexing and context building.

This package provides the core processing workers that handle code analysis
and context generation for the MCP tools.

Components:
    Indexer: Incremental file indexer with Tree-sitter parsing
    ContextBuilder: Token-budgeted context pack generator for coding tasks

Indexer Features:
    - Content hash comparison for efficient change detection
    - Symbol extraction using Tree-sitter grammars
    - Call/import relationship (edge) detection
    - .gitignore pattern respect
    - Error logging to errors.jsonl
    - Parallel processing with ThreadPoolExecutor

ContextBuilder Features:
    - Relevance ranking with configurable weights
    - Kind-based score boosts (classes > functions > variables)
    - Token budget enforcement with 5% overrun tolerance
    - Code snippet inclusion for top-ranked symbols
    - Test file detection and filtering
    - Recommendations generation based on task analysis

Data Classes:
    IndexStats: Indexing progress and completion statistics
    ContextPack: Token-budgeted context with symbols and recommendations
    RankedSymbol: Symbol with relevance score for ranking
"""

from civyk_repoix.workers.context_builder import (
    ContextBuilder,
    ContextPack,
    RankedSymbol,
    estimate_tokens,
)
from civyk_repoix.workers.indexer import (
    ErrorLogger,
    Indexer,
    IndexStats,
)

__all__ = [
    "ContextBuilder",
    "ContextPack",
    "ErrorLogger",
    "IndexStats",
    "Indexer",
    "RankedSymbol",
    "estimate_tokens",
]
