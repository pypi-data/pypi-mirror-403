"""
リクエスト/レスポンスモデル

SOLID原則に基づく設計:
- SRP: 各モデルは単一のリクエスト種別を担当
- ISP: PathRequestMixinで共通インターフェースを提供
- DRY: 共通フィールド定義をAnnotatedで抽出
"""

from typing import Annotated

from pydantic import BaseModel, Field


# 共通フィールド定義（DRY原則）
FilePath = Annotated[str, Field(min_length=1, description="ファイルパス")]
FileContent = Annotated[str, Field(description="ファイル内容")]


class PathRequestMixin(BaseModel):
    """パスを持つリクエストの共通インターフェース（ISP）"""

    path: FilePath


class SaveFileRequest(PathRequestMixin):
    """ファイル保存リクエスト"""

    content: FileContent


class CreateDirectoryRequest(PathRequestMixin):
    """フォルダ作成リクエスト"""

    pass


class MoveItemRequest(BaseModel):
    """ファイル/フォルダ移動リクエスト"""

    source: FilePath
    destination: FilePath
