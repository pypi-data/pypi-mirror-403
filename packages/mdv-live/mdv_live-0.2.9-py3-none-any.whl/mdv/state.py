"""
アプリケーション状態管理

SRP: アプリケーション状態のみを担当
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .file_types import SKIP_DIRECTORIES


@dataclass
class AppState:
    """アプリケーション状態を管理"""
    root_path: Path = field(default_factory=Path.cwd)
    current_watching_file: Optional[str] = None
    last_mtime: float = 0
    dir_mtimes: dict[str, float] = field(default_factory=dict)

    def set_root_path(self, path: str | Path) -> None:
        self.root_path = Path(path).resolve()
        self._update_dir_mtimes()

    def set_watching_file(self, path: str) -> None:
        """監視対象ファイルを設定"""
        self.current_watching_file = path
        try:
            self.last_mtime = os.path.getmtime(path)
        except OSError:
            self.last_mtime = 0

    def check_file_changed(self) -> bool:
        """監視中のファイルが変更されたかチェック"""
        if not self.current_watching_file:
            return False

        try:
            mtime = os.path.getmtime(self.current_watching_file)
            if mtime != self.last_mtime:
                self.last_mtime = mtime
                return True
        except OSError:
            pass

        return False

    def check_dir_changes(self) -> bool:
        """ディレクトリのmtime変更をチェック（変更があればTrue）"""
        changed = False

        try:
            # ルートディレクトリをチェック
            current_mtime = os.path.getmtime(self.root_path)
            if self.dir_mtimes.get(str(self.root_path)) != current_mtime:
                changed = True

            # 直下のサブディレクトリをチェック
            for entry in self.root_path.iterdir():
                if entry.is_dir() and entry.name not in SKIP_DIRECTORIES:
                    try:
                        current = os.path.getmtime(entry)
                        path_str = str(entry)
                        if path_str not in self.dir_mtimes or self.dir_mtimes[path_str] != current:
                            changed = True
                            break
                    except OSError:
                        pass
        except OSError:
            pass

        if changed:
            self._update_dir_mtimes()

        return changed

    def _update_dir_mtimes(self) -> None:
        """監視対象ディレクトリのmtimeを更新"""
        self.dir_mtimes = {}

        try:
            self.dir_mtimes[str(self.root_path)] = os.path.getmtime(self.root_path)

            for entry in self.root_path.iterdir():
                if entry.is_dir() and entry.name not in SKIP_DIRECTORIES:
                    try:
                        self.dir_mtimes[str(entry)] = os.path.getmtime(entry)
                    except OSError:
                        pass
        except OSError:
            pass


# シングルトンインスタンス
state = AppState()
