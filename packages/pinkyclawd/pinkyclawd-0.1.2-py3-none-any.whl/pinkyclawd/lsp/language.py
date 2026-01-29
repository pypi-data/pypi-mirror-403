"""
Language ID mappings for LSP.

Maps file extensions to LSP language identifiers.
"""

from __future__ import annotations

from pathlib import Path

# Map file extensions to language IDs
LANGUAGE_MAP: dict[str, str] = {
    # Python
    ".py": "python",
    ".pyi": "python",
    ".pyw": "python",
    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "javascriptreact",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescriptreact",
    ".mts": "typescript",
    ".cts": "typescript",
    # Web
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".vue": "vue",
    ".svelte": "svelte",
    # Rust
    ".rs": "rust",
    # Go
    ".go": "go",
    ".mod": "go.mod",
    # C/C++
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",
    # C#
    ".cs": "csharp",
    # Java
    ".java": "java",
    # Kotlin
    ".kt": "kotlin",
    ".kts": "kotlin",
    # Swift
    ".swift": "swift",
    # Ruby
    ".rb": "ruby",
    ".erb": "erb",
    ".rake": "ruby",
    ".gemspec": "ruby",
    # PHP
    ".php": "php",
    # Lua
    ".lua": "lua",
    # Perl
    ".pl": "perl",
    ".pm": "perl",
    # R
    ".r": "r",
    ".R": "r",
    # Shell
    ".sh": "shellscript",
    ".bash": "shellscript",
    ".zsh": "shellscript",
    ".fish": "fish",
    # PowerShell
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".psd1": "powershell",
    # SQL
    ".sql": "sql",
    # Markdown
    ".md": "markdown",
    ".markdown": "markdown",
    # JSON/YAML/TOML
    ".json": "json",
    ".jsonc": "jsonc",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    # XML
    ".xml": "xml",
    ".xsd": "xml",
    ".xsl": "xml",
    ".xslt": "xml",
    ".svg": "xml",
    # LaTeX
    ".tex": "latex",
    ".bib": "bibtex",
    # Haskell
    ".hs": "haskell",
    ".lhs": "haskell",
    # Elixir
    ".ex": "elixir",
    ".exs": "elixir",
    # Erlang
    ".erl": "erlang",
    ".hrl": "erlang",
    # Clojure
    ".clj": "clojure",
    ".cljs": "clojurescript",
    ".cljc": "clojure",
    ".edn": "clojure",
    # Scala
    ".scala": "scala",
    ".sc": "scala",
    # F#
    ".fs": "fsharp",
    ".fsi": "fsharp",
    ".fsx": "fsharp",
    # OCaml
    ".ml": "ocaml",
    ".mli": "ocaml",
    # Dart
    ".dart": "dart",
    # Julia
    ".jl": "julia",
    # Nim
    ".nim": "nim",
    # Zig
    ".zig": "zig",
    # Dockerfile
    "Dockerfile": "dockerfile",
    ".dockerfile": "dockerfile",
    # Terraform
    ".tf": "terraform",
    ".tfvars": "terraform",
    # Makefile
    "Makefile": "makefile",
    ".mk": "makefile",
    # CMake
    "CMakeLists.txt": "cmake",
    ".cmake": "cmake",
    # Protocol Buffers
    ".proto": "proto",
    # GraphQL
    ".graphql": "graphql",
    ".gql": "graphql",
    # GLSL
    ".glsl": "glsl",
    ".vert": "glsl",
    ".frag": "glsl",
}


def get_language_id(file_path: str | Path) -> str | None:
    """
    Get the LSP language ID for a file.

    Args:
        file_path: Path to the file

    Returns:
        Language ID or None if unknown
    """
    path = Path(file_path)
    name = path.name

    # Check full filename first (for Dockerfile, Makefile, etc.)
    if name in LANGUAGE_MAP:
        return LANGUAGE_MAP[name]

    # Check extension
    suffix = path.suffix.lower()
    return LANGUAGE_MAP.get(suffix)


def get_file_extension(language_id: str) -> str | None:
    """
    Get a common file extension for a language ID.

    Args:
        language_id: LSP language ID

    Returns:
        File extension or None if unknown
    """
    # Reverse lookup - prefer common extensions
    preferred = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "javascriptreact": ".jsx",
        "typescriptreact": ".tsx",
        "rust": ".rs",
        "go": ".go",
        "c": ".c",
        "cpp": ".cpp",
        "csharp": ".cs",
        "java": ".java",
        "kotlin": ".kt",
        "swift": ".swift",
        "ruby": ".rb",
        "php": ".php",
        "html": ".html",
        "css": ".css",
        "json": ".json",
        "yaml": ".yaml",
        "markdown": ".md",
    }

    if language_id in preferred:
        return preferred[language_id]

    # Find first matching extension
    for ext, lang in LANGUAGE_MAP.items():
        if lang == language_id:
            return ext if ext.startswith(".") else f".{ext}"

    return None
