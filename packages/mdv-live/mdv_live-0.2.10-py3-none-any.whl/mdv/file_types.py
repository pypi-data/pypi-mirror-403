"""
ファイルタイプの定義

SOLID/DRY原則に基づいた設計:
- OCP: FILE_TYPE_REGISTRY に追加するだけで新しいファイルタイプをサポート
- DRY: 同じタイプの拡張子をグループ化して重複を排除
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FileTypeInfo:
    """ファイルタイプ情報"""

    type: str  # 'markdown', 'text', 'code', 'image', etc.
    icon: str
    lang: Optional[str] = None


# ファイルタイプ定義レジストリ
# 新しいタイプを追加する場合はここにエントリを追加するだけでOK (OCP)
FILE_TYPE_REGISTRY: tuple[tuple[FileTypeInfo, tuple[str, ...]], ...] = (
    # Markdown
    (FileTypeInfo("markdown", "markdown"), (".md", ".markdown")),
    # Text
    (FileTypeInfo("text", "text"), (".txt", ".text", ".rst", ".log")),
    # Config - JSON
    (FileTypeInfo("code", "json", "json"), (".json",)),
    # Config - YAML
    (FileTypeInfo("code", "yaml", "yaml"), (".yaml", ".yml")),
    # Config - TOML
    (FileTypeInfo("code", "toml", "toml"), (".toml",)),
    # Config - INI
    (FileTypeInfo("code", "config", "ini"), (".ini", ".cfg", ".conf")),
    # Config - ENV
    (FileTypeInfo("code", "config", "bash"), (".env",)),
    # Python
    (FileTypeInfo("code", "python", "python"), (".py",)),
    # JavaScript
    (FileTypeInfo("code", "javascript", "javascript"), (".js",)),
    # TypeScript
    (FileTypeInfo("code", "typescript", "typescript"), (".ts",)),
    # React
    (FileTypeInfo("code", "react", "javascript"), (".jsx",)),
    (FileTypeInfo("code", "react", "typescript"), (".tsx",)),
    # HTML
    (FileTypeInfo("code", "html", "html"), (".html",)),
    # CSS
    (FileTypeInfo("code", "css", "css"), (".css",)),
    (FileTypeInfo("code", "css", "scss"), (".scss",)),
    (FileTypeInfo("code", "css", "less"), (".less",)),
    # Java
    (FileTypeInfo("code", "java", "java"), (".java",)),
    # C/C++
    (FileTypeInfo("code", "c", "c"), (".c", ".h")),
    (FileTypeInfo("code", "cpp", "cpp"), (".cpp", ".hpp")),
    # Go
    (FileTypeInfo("code", "go", "go"), (".go",)),
    # Rust
    (FileTypeInfo("code", "rust", "rust"), (".rs",)),
    # Ruby
    (FileTypeInfo("code", "ruby", "ruby"), (".rb",)),
    # PHP
    (FileTypeInfo("code", "php", "php"), (".php",)),
    # Swift
    (FileTypeInfo("code", "swift", "swift"), (".swift",)),
    # Kotlin
    (FileTypeInfo("code", "kotlin", "kotlin"), (".kt",)),
    # Shell
    (FileTypeInfo("code", "shell", "bash"), (".sh", ".bash", ".zsh")),
    # SQL
    (FileTypeInfo("code", "database", "sql"), (".sql",)),
    # XML
    (FileTypeInfo("code", "xml", "xml"), (".xml",)),
    # GraphQL
    (FileTypeInfo("code", "graphql", "graphql"), (".graphql",)),
    # Vue
    (FileTypeInfo("code", "vue", "html"), (".vue",)),
    # Svelte
    (FileTypeInfo("code", "svelte", "html"), (".svelte",)),
    # Jinja2 Templates
    (FileTypeInfo("code", "jinja2", "django"), (".j2", ".jinja", ".jinja2")),
    # Images (DRY: 1つのFileTypeInfoで8拡張子をカバー)
    (
        FileTypeInfo("image", "image"),
        (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp"),
    ),
    # PDF
    (FileTypeInfo("pdf", "pdf"), (".pdf",)),
    # Video (DRY: 1つのFileTypeInfoで6拡張子をカバー)
    (FileTypeInfo("video", "video"), (".mp4", ".webm", ".mov", ".avi", ".mkv", ".m4v")),
    # Audio (DRY: 1つのFileTypeInfoで6拡張子をカバー)
    (FileTypeInfo("audio", "audio"), (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac")),
    # Archive
    (FileTypeInfo("archive", "archive"), (".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".rar", ".7z")),
    # Office
    (FileTypeInfo("office", "office"), (".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp")),
    # Executable / Installer
    (FileTypeInfo("executable", "executable"), (".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".app")),
    # Other binary
    (FileTypeInfo("binary", "binary"), (".bin", ".dat", ".iso", ".img")),
)


def _build_file_types_dict() -> dict[str, FileTypeInfo]:
    """レジストリから拡張子マッピング辞書を構築"""
    result: dict[str, FileTypeInfo] = {}
    for file_type_info, extensions in FILE_TYPE_REGISTRY:
        for ext in extensions:
            result[ext] = file_type_info
    return result


# ファイル拡張子とタイプのマッピング (後方互換性のため維持)
FILE_TYPES: dict[str, FileTypeInfo] = _build_file_types_dict()

# サポートする拡張子のセット
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(FILE_TYPES.keys())

# スキップするディレクトリ
SKIP_DIRECTORIES: frozenset[str] = frozenset(
    [
        "node_modules",
        "__pycache__",
        "venv",
        ".venv",
        ".git",
        "dist",
        "build",
        ".next",
        ".nuxt",
        ".cache",
        "coverage",
        ".pytest_cache",
        ".mypy_cache",
        ".Trash",
        ".Trashes",
        "Library",
        "OneDrive",
        "Dropbox",
        "Google Drive",
        "iCloud Drive",
    ]
)

# スキップするファイル（ゴミファイル）
SKIP_FILES: frozenset[str] = frozenset(
    [
        ".DS_Store",
        ".localized",
        "Thumbs.db",
        "desktop.ini",
    ]
)


def get_file_type(extension: str) -> Optional[FileTypeInfo]:
    """拡張子からファイルタイプ情報を取得"""
    return FILE_TYPES.get(extension.lower())
