"""
ファイル監視機能

SRP: ファイル変更監視のみを担当
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, Awaitable

if TYPE_CHECKING:
    from .state import AppState
    from .websocket_manager import WebSocketManager


async def file_watcher(
    state: "AppState",
    ws_manager: "WebSocketManager",
    on_file_change: Callable[[str], Awaitable[None]],
    on_tree_change: Callable[[], Awaitable[None]],
    poll_interval: float = 0.3,
    dir_check_frequency: int = 3,
) -> None:
    """ファイル変更を監視（ポーリング方式）

    Args:
        state: アプリケーション状態
        ws_manager: WebSocketマネージャー
        on_file_change: ファイル変更時のコールバック
        on_tree_change: ディレクトリ変更時のコールバック
        poll_interval: ポーリング間隔（秒）
        dir_check_frequency: ディレクトリチェック頻度（N回に1回）
    """
    dir_check_counter = 0

    while True:
        await asyncio.sleep(poll_interval)

        if not ws_manager.has_clients:
            continue

        # ファイル変更チェック
        if state.check_file_changed() and state.current_watching_file:
            await on_file_change(state.current_watching_file)

        # ディレクトリ変更チェック（N回に1回）
        dir_check_counter += 1
        if dir_check_counter >= dir_check_frequency:
            dir_check_counter = 0
            if state.check_dir_changes():
                await on_tree_change()
