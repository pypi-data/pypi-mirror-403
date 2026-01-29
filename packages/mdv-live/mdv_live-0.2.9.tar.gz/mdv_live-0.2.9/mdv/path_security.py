"""
パス検証・セキュリティ機能

SRP: パスのセキュリティ検証のみを担当
"""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException


def validate_path(requested_path: str, root_path: Path) -> Path:
    """パスを検証してセキュアなPathオブジェクトを返す

    Args:
        requested_path: リクエストされたパス
        root_path: 許可されたルートパス

    Returns:
        検証済みのPathオブジェクト

    Raises:
        HTTPException: ファイルが存在しないか、アクセス権限がない場合
    """
    file_path = root_path / requested_path

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    _validate_within_root(file_path, root_path)

    return file_path


def validate_path_for_write(requested_path: str, root_path: Path) -> Path:
    """書き込み用のパス検証（ファイルが存在しなくてもOK）

    Args:
        requested_path: リクエストされたパス
        root_path: 許可されたルートパス

    Returns:
        検証済みのPathオブジェクト

    Raises:
        HTTPException: アクセス権限がない場合
    """
    file_path = root_path / requested_path
    _validate_within_root(file_path, root_path)
    return file_path


def _validate_within_root(file_path: Path, root_path: Path) -> None:
    """パスがルートパス内にあることを確認"""
    try:
        file_path.resolve().relative_to(root_path.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")


def sanitize_filename(filename: str) -> str:
    """ファイル名をサニタイズ（パス区切り文字を除去）"""
    return Path(filename).name
