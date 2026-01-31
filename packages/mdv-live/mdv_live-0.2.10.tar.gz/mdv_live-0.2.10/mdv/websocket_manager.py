"""
WebSocket接続管理とブロードキャスト機能

SRP: WebSocket通信のみを担当
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Set

from fastapi import WebSocket

if TYPE_CHECKING:
    pass


class WebSocketManager:
    """WebSocket接続の管理とブロードキャストを担当"""

    def __init__(self) -> None:
        self._clients: Set[WebSocket] = set()

    @property
    def clients(self) -> Set[WebSocket]:
        return self._clients

    @property
    def has_clients(self) -> bool:
        return len(self._clients) > 0

    def add(self, client: WebSocket) -> None:
        self._clients.add(client)

    def remove(self, client: WebSocket) -> None:
        self._clients.discard(client)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """全クライアントにメッセージを送信"""
        if not self._clients:
            return

        message_json = json.dumps(message)
        disconnected: list[WebSocket] = []

        for client in self._clients:
            try:
                await client.send_text(message_json)
            except Exception:
                disconnected.append(client)

        # 切断されたクライアントを削除
        for client in disconnected:
            self.remove(client)


# シングルトンインスタンス
ws_manager = WebSocketManager()
