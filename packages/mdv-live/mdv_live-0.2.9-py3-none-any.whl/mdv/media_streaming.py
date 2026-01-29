"""
メディアストリーミング機能

SRP: 動画/音声のストリーミングのみを担当
"""

from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from typing import Generator, Optional

from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse


# ストリーミングのチャンクサイズ (1MB)
CHUNK_SIZE = 1024 * 1024


def _parse_range_header(range_header: str) -> tuple[Optional[int], Optional[int]]:
    """Range ヘッダーをパース"""
    match = re.match(r"bytes=(\d*)-(\d*)", range_header)
    if not match:
        return None, None

    start = int(match.group(1)) if match.group(1) else None
    end = int(match.group(2)) if match.group(2) else None
    return start, end


def _stream_range(file_path: Path, start: int, content_length: int) -> Generator[bytes, None, None]:
    """指定範囲のファイルをストリーミング"""
    with open(file_path, "rb") as f:
        f.seek(start)
        remaining = content_length

        while remaining > 0:
            chunk_size = min(CHUNK_SIZE, remaining)
            chunk = f.read(chunk_size)
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


def _stream_file(file_path: Path) -> Generator[bytes, None, None]:
    """ファイル全体をストリーミング"""
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            yield chunk


def create_streaming_response(
    file_path: Path,
    request: Optional[Request] = None
) -> StreamingResponse:
    """メディアファイルのストリーミングレスポンスを生成

    Args:
        file_path: ファイルパス
        request: HTTPリクエスト（Rangeヘッダー取得用）

    Returns:
        StreamingResponse

    Raises:
        HTTPException: ファイルが存在しないか、Range指定が不正な場合
    """
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    file_size = file_path.stat().st_size
    mime_type, _ = mimetypes.guess_type(str(file_path))
    mime_type = mime_type or "application/octet-stream"

    range_header = request.headers.get("range") if request else None

    # Range指定がある場合
    if range_header:
        start, end = _parse_range_header(range_header)

        if start is not None:
            if start >= file_size:
                raise HTTPException(status_code=416, detail="Range not satisfiable")

            end = min(end, file_size - 1) if end is not None else file_size - 1
            content_length = end - start + 1

            return StreamingResponse(
                _stream_range(file_path, start, content_length),
                status_code=206,
                media_type=mime_type,
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(content_length),
                }
            )

    # Range指定なしの場合は全体を返す
    return StreamingResponse(
        _stream_file(file_path),
        media_type=mime_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
        }
    )
