from typing import Final

SUPPORTED_LANGUAGES: Final[tuple[tuple[str, str], ...]] = (
    ("Python", ".py"),
    ("Java", ".java"),
    ("JavaScript", ".js"),
    ("TypeScript", ".ts"),
    ("Go", ".go"),
    ("Rust", ".rs"),
    ("Kotlin", ".kt"),
    ("Ruby", ".rb"),
    ("Dart", ".dart"),
    ("C#", ".cs"),
)
"""
Supported languages and their file extensions.

Python has first-class support, expecting the best formalization performance.

Languages other than above won't be rejected, but formalization performance
might be suboptimal.
"""
