"""Parsing engines for code analysis.

This package provides the language parsing infrastructure using Tree-sitter
for efficient, accurate parsing of source code across multiple programming
languages.

Components:
    TreeSitterEngine: Main parsing engine with thread-safe parser caching
    ParseResult: Container for extracted symbols, references, and errors

Supported Languages:
    Tier 1 (Primary): Python, JavaScript, TypeScript, TSX
    Tier 2 (Common): Java, Go, C#, Rust, Ruby, PHP
    Tier 3 (SQL): SQL with T-SQL/PL/SQL dialect detection
    Tier 4 (Config): JSON, YAML, TOML, XML
    Tier 5 (Docs): Markdown

Key Features:
    - Symbol extraction (classes, functions, methods, etc.)
    - Reference detection (calls, imports, type annotations)
    - Docstring extraction for multiple documentation styles
    - Language-specific visibility detection (public/private)
    - Thread-safe parsing with per-thread parser instances
"""

from civyk_repoix.engines.languages import (
    LANGUAGE_EXTENSIONS,
    detect_language,
    get_language,
    get_supported_languages,
    is_supported,
)
from civyk_repoix.engines.treesitter import ParseResult, TreeSitterEngine

__all__ = [
    "LANGUAGE_EXTENSIONS",
    "ParseResult",
    "TreeSitterEngine",
    "detect_language",
    "get_language",
    "get_supported_languages",
    "is_supported",
]
