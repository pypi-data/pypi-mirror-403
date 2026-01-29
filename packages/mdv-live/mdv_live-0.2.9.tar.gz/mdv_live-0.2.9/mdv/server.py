"""
MDV - Markdown Viewer Server
ファイルツリー表示 + マークダウンプレビュー + ホットリロード

リファクタリング: SOLID/DRY原則に基づき責任を分離
- state.py: アプリケーション状態管理
- websocket_manager.py: WebSocket接続管理
- rendering.py: Markdown/コードレンダリング
- file_tree.py: ファイルツリー構築
- path_security.py: パス検証・セキュリティ
- file_response.py: APIレスポンス生成
- media_streaming.py: メディアストリーミング
- watcher.py: ファイル監視
"""

from __future__ import annotations

import asyncio
import json
import mimetypes
import shutil
import socket
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import FileResponse as FastAPIFileResponse
from fastapi.staticfiles import StaticFiles

from .file_response import build_file_response, build_file_update_message
from .file_tree import build_file_tree
from .file_types import get_file_type
from .media_streaming import create_streaming_response
from .path_security import validate_path, validate_path_for_write, sanitize_filename
from .models import SaveFileRequest, CreateDirectoryRequest, MoveItemRequest
from .state import state
from .watcher import file_watcher
from .websocket_manager import ws_manager


# === Broadcast Functions ===

async def broadcast_tree_update() -> None:
    """全クライアントにファイルツリー更新を通知"""
    try:
        tree = build_file_tree(state.root_path, state.root_path)
        await ws_manager.broadcast({"type": "tree_update", "tree": tree})
    except Exception as e:
        print(f"Error broadcasting tree update: {e}")


async def broadcast_file_update(file_path: str) -> None:
    """全クライアントにファイル更新を通知"""
    try:
        message = build_file_update_message(file_path, Path(file_path))
        if message:
            await ws_manager.broadcast(message)
    except Exception as e:
        print(f"Error broadcasting update: {e}")


# === FastAPI Application ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    asyncio.create_task(
        file_watcher(
            state=state,
            ws_manager=ws_manager,
            on_file_change=broadcast_file_update,
            on_tree_change=broadcast_tree_update,
        )
    )
    print("File watcher started (polling mode)")
    yield
    print("Server shutting down")


app = FastAPI(title="MDV - Markdown Viewer", lifespan=lifespan)


# === Static Files ===

static_dir = Path(__file__).parent / "static"


@app.get("/")
async def index() -> FastAPIFileResponse:
    """メインページ"""
    return FastAPIFileResponse(static_dir / "index.html")


# === API: File Tree ===

@app.get("/api/tree")
async def get_tree() -> list:
    """ファイルツリーを取得（1階層のみ、遅延読み込み対応）"""
    return build_file_tree(state.root_path, state.root_path, max_depth=1)


@app.get("/api/tree/expand")
async def expand_tree(path: str = Query(...)) -> list:
    """指定ディレクトリの子要素を取得（遅延読み込み用）"""
    dir_path = validate_path(path, state.root_path)

    if not dir_path.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")

    return build_file_tree(dir_path, state.root_path, max_depth=1)


@app.get("/api/info")
async def get_info() -> dict:
    """サーバー情報を取得"""
    return {
        "rootPath": str(state.root_path),
        "rootName": state.root_path.name or str(state.root_path)
    }


@app.post("/api/shutdown")
async def shutdown() -> dict:
    """サーバーをシャットダウン"""
    import os
    import signal

    async def delayed_shutdown():
        await asyncio.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)

    asyncio.create_task(delayed_shutdown())
    return {"success": True, "message": "Server shutting down..."}


# === API: File Operations ===

@app.get("/api/file")
async def get_file(path: str = Query(...)) -> dict:
    """ファイルを取得してレンダリング"""
    file_path = validate_path(path, state.root_path)

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    # 監視対象を更新
    state.set_watching_file(str(file_path.resolve()))

    return build_file_response(path, file_path)


@app.post("/api/file")
async def save_file(request: SaveFileRequest) -> dict:
    """ファイルを保存"""
    file_path = validate_path(request.path, state.root_path)

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    file_info = get_file_type(file_path.suffix)
    if not file_info or file_info.type == "image":
        raise HTTPException(status_code=400, detail="Cannot edit this file type")

    try:
        file_path.write_text(request.content, encoding="utf-8")
        return {"success": True, "path": request.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")


@app.delete("/api/file")
async def delete_file(path: str = Query(...)) -> dict:
    """ファイルまたはフォルダを削除"""
    file_path = validate_path(path, state.root_path)

    try:
        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            file_path.unlink()
        await broadcast_tree_update()
        return {"success": True, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


@app.get("/api/download")
async def download_file(path: str = Query(...)) -> FastAPIFileResponse:
    """ファイルをダウンロード"""
    file_path = validate_path(path, state.root_path)

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    mime_type, _ = mimetypes.guess_type(str(file_path))
    return FastAPIFileResponse(
        file_path,
        media_type=mime_type or "application/octet-stream",
        filename=file_path.name
    )


# === API: Media Files ===

@app.get("/api/image")
async def get_image(path: str = Query(...)) -> FastAPIFileResponse:
    """画像ファイルを返す"""
    file_path = validate_path(path, state.root_path)

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type or not mime_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Not an image file")

    return FastAPIFileResponse(file_path, media_type=mime_type)


@app.get("/api/pdf")
async def get_pdf(path: str = Query(...)) -> FastAPIFileResponse:
    """PDFファイルを返す"""
    file_path = validate_path(path, state.root_path)

    if file_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Not a PDF file")

    return FastAPIFileResponse(file_path, media_type="application/pdf")


@app.get("/api/media")
async def get_media(path: str = Query(...), request: Request = None):
    """動画/音声ストリーミング（Range requests対応）"""
    file_path = validate_path(path, state.root_path)
    return create_streaming_response(file_path, request)


# === API: File Management ===

# アップロードファイルサイズ制限（100MB）
MAX_UPLOAD_SIZE = 100 * 1024 * 1024


@app.post("/api/upload")
async def upload_files(
    path: str = Form(""),
    files: List[UploadFile] = File(...)
) -> dict:
    """ファイルをアップロード（複数ファイル対応、100MBまで）"""
    target_dir = validate_path_for_write(path, state.root_path) if path else state.root_path
    target_dir.mkdir(parents=True, exist_ok=True)

    if not target_dir.is_dir():
        raise HTTPException(status_code=400, detail="Target is not a directory")

    uploaded = []
    for file in files:
        if not file.filename:
            continue

        # ファイルサイズチェック
        file.file.seek(0, 2)  # ファイル末尾に移動
        file_size = file.file.tell()
        file.file.seek(0)  # 先頭に戻す
        if file_size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File '{file.filename}' exceeds maximum size of 100MB"
            )

        filename = sanitize_filename(file.filename)
        dest_path = target_dir / filename

        try:
            with open(dest_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            uploaded.append(filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload {filename}: {str(e)}")

    if uploaded:
        await broadcast_tree_update()

    return {"success": True, "uploaded": uploaded}


@app.post("/api/mkdir")
async def create_directory(request: CreateDirectoryRequest) -> dict:
    """新規フォルダを作成"""
    dir_path = validate_path_for_write(request.path, state.root_path)

    if dir_path.exists():
        raise HTTPException(status_code=400, detail="Directory already exists")

    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        await broadcast_tree_update()
        return {"success": True, "path": request.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")


@app.post("/api/move")
async def move_item(request: MoveItemRequest) -> dict:
    """ファイル/フォルダを移動またはリネーム"""
    source_path = validate_path(request.source, state.root_path)
    dest_path = validate_path_for_write(request.destination, state.root_path)

    if dest_path.exists():
        raise HTTPException(status_code=400, detail="Destination already exists")

    try:
        shutil.move(str(source_path), str(dest_path))
        await broadcast_tree_update()
        return {"success": True, "source": request.source, "destination": request.destination}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to move: {str(e)}")


# === WebSocket ===

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket接続を管理"""
    await websocket.accept()
    ws_manager.add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "watch":
                try:
                    file_path = validate_path(message.get("path", ""), state.root_path)
                    state.set_watching_file(str(file_path.resolve()))
                except HTTPException:
                    pass  # 無効なパスは無視

    except WebSocketDisconnect:
        ws_manager.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.remove(websocket)


# === Static Files Mount ===

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# === Server Startup ===

def find_available_port(start_port: int, max_attempts: int = 100) -> int:
    """利用可能なポートを探す"""
    for offset in range(max_attempts):
        port = start_port + offset
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue

    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_attempts}")


def start_server(
    root_path: str = ".",
    port: int = 8642,
    open_browser: bool = True,
    initial_file: Optional[str] = None,
) -> None:
    """サーバーを起動"""
    state.set_root_path(root_path)

    if not state.root_path.exists():
        print(f"Error: Path does not exist: {state.root_path}")
        return

    try:
        actual_port = find_available_port(port)
        if actual_port != port:
            print(f"Port {port} is in use, using {actual_port} instead")
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    print(f"Serving: {state.root_path}")
    print(f"URL: http://localhost:{actual_port}")

    if open_browser:
        import threading
        from urllib.parse import quote

        url = f"http://localhost:{actual_port}"
        if initial_file:
            url += f"?file={quote(initial_file)}"

        def open_browser_delayed():
            import time
            time.sleep(0.5)
            webbrowser.open(url)

        threading.Thread(target=open_browser_delayed, daemon=True).start()

    try:
        config = uvicorn.Config(app, host="127.0.0.1", port=actual_port, log_level="warning")
        server = uvicorn.Server(config)
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    start_server()
