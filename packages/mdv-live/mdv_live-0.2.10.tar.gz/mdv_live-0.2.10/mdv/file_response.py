"""
ファイルレスポンス生成機能

SRP: APIレスポンス生成のみを担当
OCP: 新しいファイルタイプはハンドラを追加するだけで対応可能
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException

from .file_types import FileTypeInfo, get_file_type
from .rendering import render_file_content


# === File Response Handlers ===

def _create_media_response(
    path: str,
    file_path: Path,
    file_info: FileTypeInfo,
    url_template: str
) -> dict[str, Any]:
    """メディアファイル（画像・PDF・動画・音声）のレスポンスを生成"""
    return {
        "path": path,
        "name": file_path.name,
        "fileType": file_info.type,
        url_template: f"/api/{file_info.type}?path={path}" if file_info.type != "video" and file_info.type != "audio" else f"/api/media?path={path}",
    }


def _create_text_response(
    path: str,
    file_path: Path,
    file_info: FileTypeInfo,
    content: str
) -> dict[str, Any]:
    """テキスト系ファイルのレスポンスを生成"""
    html_content = render_file_content(content, file_info)
    return {
        "path": path,
        "name": file_path.name,
        "content": html_content,
        "raw": content,
        "fileType": file_info.type,
        "lang": file_info.lang,
    }


# ファイルタイプとURLキーのマッピング
_MEDIA_URL_KEYS = {
    "image": "imageUrl",
    "pdf": "pdfUrl",
    "video": "mediaUrl",
    "audio": "mediaUrl",
}


def build_file_response(path: str, file_path: Path) -> dict[str, Any]:
    """ファイルパスからAPIレスポンスを生成

    Args:
        path: 相対パス
        file_path: 絶対ファイルパス

    Returns:
        APIレスポンス用辞書

    Raises:
        HTTPException: サポートされていないファイルタイプの場合
    """
    file_info = get_file_type(file_path.suffix)
    if not file_info:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # バイナリ系ファイルの場合（表示のみ）
    if file_info.type in ("archive", "office", "executable", "binary"):
        return {
            "path": path,
            "name": file_path.name,
            "fileType": file_info.type,
        }

    # メディアファイルの場合
    url_key = _MEDIA_URL_KEYS.get(file_info.type)
    if url_key:
        url_path_map = {
            "image": "/api/image",
            "pdf": "/api/pdf",
            "video": "/api/media",
            "audio": "/api/media",
        }
        url_path = url_path_map.get(file_info.type, "/api/media")
        return {
            "path": path,
            "name": file_path.name,
            "fileType": file_info.type,
            url_key: f"{url_path}?path={path}",
        }

    # テキスト系ファイルの場合
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Cannot read binary file as text")

    return _create_text_response(path, file_path, file_info, content)


def build_file_update_message(file_path: str, path: Path) -> Optional[dict[str, Any]]:
    """ファイル更新通知用のメッセージを生成

    Args:
        file_path: ファイルパス文字列
        path: Pathオブジェクト

    Returns:
        WebSocket通知用のメッセージ、またはNone
    """
    file_info = get_file_type(path.suffix)
    if not file_info:
        return None

    if file_info.type == "image":
        return {
            "type": "file_update",
            "path": file_path,
            "fileType": "image",
            "reload": True,
        }

    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None

    html_content = render_file_content(content, file_info)
    return {
        "type": "file_update",
        "path": file_path,
        "content": html_content,
        "raw": content,
        "fileType": file_info.type,
    }
