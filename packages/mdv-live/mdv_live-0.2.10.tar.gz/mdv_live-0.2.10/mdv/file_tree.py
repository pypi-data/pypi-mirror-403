"""
ファイルツリー構築機能

SRP: ファイルツリー構築のみを担当
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .file_types import (
    FILE_TYPES,
    SUPPORTED_EXTENSIONS,
    SKIP_DIRECTORIES,
    SKIP_FILES,
)


def build_file_tree(
    root: Path,
    base_path: Path,
    max_depth: int = 1,
    current_depth: int = 0
) -> list[dict[str, Any]]:
    """ディレクトリツリーを構築

    Args:
        root: 走査するディレクトリ
        base_path: 相対パス計算の基準ディレクトリ
        max_depth: 最大深さ（1=直下のみ、0=無制限）
        current_depth: 現在の深さ（内部用）

    Returns:
        ファイルツリー構造のリスト
    """
    items: list[dict[str, Any]] = []

    try:
        entries = sorted(
            root.iterdir(),
            key=lambda x: (not x.is_dir(), x.name.lower())
        )
    except (PermissionError, OSError, TimeoutError):
        return items

    for entry in entries:
        if entry.name in SKIP_DIRECTORIES or entry.name in SKIP_FILES:
            continue

        rel_path = str(entry.relative_to(base_path))

        if entry.is_dir():
            items.append(_build_directory_node(entry, rel_path, base_path, max_depth, current_depth))
        elif entry.suffix.lower() in SUPPORTED_EXTENSIONS:
            items.append(_build_file_node(entry, rel_path))

    return items


def _build_directory_node(
    entry: Path,
    rel_path: str,
    base_path: Path,
    max_depth: int,
    current_depth: int
) -> dict[str, Any]:
    """ディレクトリノードを構築"""
    # 深さ制限チェック
    if max_depth > 0 and current_depth >= max_depth:
        return {
            "name": entry.name,
            "path": rel_path,
            "type": "directory",
            "children": [],
            "loaded": False,
        }

    children = build_file_tree(entry, base_path, max_depth, current_depth + 1)
    return {
        "name": entry.name,
        "path": rel_path,
        "type": "directory",
        "children": children,
        "loaded": True,
    }


def _build_file_node(entry: Path, rel_path: str) -> dict[str, Any]:
    """ファイルノードを構築"""
    file_info = FILE_TYPES[entry.suffix.lower()]
    return {
        "name": entry.name,
        "path": rel_path,
        "type": "file",
        "fileType": file_info.type,
        "icon": file_info.icon,
        "lang": file_info.lang,
    }
