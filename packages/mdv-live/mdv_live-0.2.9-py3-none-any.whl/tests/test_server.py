"""
MDV Server Tests
"""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mdv.server import app
from mdv.state import state


@pytest.fixture
def temp_dir():
    """テスト用一時ディレクトリ"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # テスト用ファイルを作成
        readme = Path(tmpdir) / "README.md"
        readme.write_text("# Hello\n\nThis is a test.")

        code_file = Path(tmpdir) / "test.py"
        code_file.write_text("print('hello')")

        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        (subdir / "nested.md").write_text("# Nested")

        yield tmpdir


@pytest.fixture
def client(temp_dir):
    """テストクライアント"""
    state.set_root_path(temp_dir)
    state.last_mtime = 0
    state.current_watching_file = None
    return TestClient(app)


class TestAPIEndpoints:
    """API エンドポイントのテスト"""

    def test_index(self, client):
        """/ エンドポイント"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_get_tree(self, client, temp_dir):
        """/api/tree エンドポイント"""
        response = client.get("/api/tree")
        assert response.status_code == 200

        tree = response.json()
        assert isinstance(tree, list)

        # ファイルが含まれていることを確認
        names = [item["name"] for item in tree]
        assert "README.md" in names
        assert "test.py" in names
        assert "subdir" in names

    def test_get_info(self, client, temp_dir):
        """/api/info エンドポイント"""
        response = client.get("/api/info")
        assert response.status_code == 200

        info = response.json()
        assert "rootPath" in info
        assert "rootName" in info

    def test_get_file_markdown(self, client, temp_dir):
        """/api/file - Markdownファイル"""
        response = client.get("/api/file", params={"path": "README.md"})
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "README.md"
        assert data["fileType"] == "markdown"
        assert "content" in data
        assert "raw" in data
        assert "<h1" in data["content"]  # HTMLに変換されている

    def test_get_file_code(self, client, temp_dir):
        """/api/file - コードファイル"""
        response = client.get("/api/file", params={"path": "test.py"})
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "test.py"
        assert data["fileType"] == "code"

    def test_get_file_nested(self, client, temp_dir):
        """/api/file - ネストされたファイル"""
        response = client.get("/api/file", params={"path": "subdir/nested.md"})
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "nested.md"

    def test_get_file_not_found(self, client):
        """/api/file - 存在しないファイル"""
        response = client.get("/api/file", params={"path": "nonexistent.md"})
        assert response.status_code == 404

    def test_get_file_path_traversal(self, client, temp_dir):
        """/api/file - パストラバーサル防止"""
        response = client.get("/api/file", params={"path": "../../../etc/passwd"})
        assert response.status_code in [403, 404]

    def test_save_file(self, client, temp_dir):
        """/api/file POST - ファイル保存"""
        new_content = "# Updated\n\nNew content here."
        response = client.post(
            "/api/file",
            json={"path": "README.md", "content": new_content}
        )
        assert response.status_code == 200

        # 実際にファイルが更新されたか確認
        readme = Path(temp_dir) / "README.md"
        assert readme.read_text() == new_content

    def test_delete_file(self, client, temp_dir):
        """/api/file DELETE - ファイル削除"""
        # テスト用ファイルを作成
        test_file = Path(temp_dir) / "to_delete.md"
        test_file.write_text("delete me")

        response = client.delete("/api/file", params={"path": "to_delete.md"})
        assert response.status_code == 200
        assert not test_file.exists()

    def test_create_directory(self, client, temp_dir):
        """/api/mkdir - ディレクトリ作成"""
        response = client.post("/api/mkdir", json={"path": "new_folder"})
        assert response.status_code == 200

        new_dir = Path(temp_dir) / "new_folder"
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_move_file(self, client, temp_dir):
        """/api/move - ファイル移動"""
        # テスト用ファイルを作成
        source = Path(temp_dir) / "source.md"
        source.write_text("source content")

        response = client.post(
            "/api/move",
            json={"source": "source.md", "destination": "moved.md"}
        )
        assert response.status_code == 200

        assert not source.exists()
        assert (Path(temp_dir) / "moved.md").exists()


class TestMarkdownRendering:
    """Markdownレンダリングのテスト"""

    def test_basic_markdown(self, client, temp_dir):
        """基本的なMarkdown変換"""
        md_file = Path(temp_dir) / "test.md"
        md_file.write_text("# Heading\n\n**bold** and *italic*")

        response = client.get("/api/file", params={"path": "test.md"})
        content = response.json()["content"]

        assert "<h1" in content
        assert "<strong>bold</strong>" in content
        assert "<em>italic</em>" in content

    def test_code_block(self, client, temp_dir):
        """コードブロックの変換"""
        md_file = Path(temp_dir) / "code.md"
        md_file.write_text("```python\nprint('hello')\n```")

        response = client.get("/api/file", params={"path": "code.md"})
        content = response.json()["content"]

        assert "<pre>" in content
        assert "<code" in content
        assert "language-python" in content

    def test_yaml_frontmatter(self, client, temp_dir):
        """YAMLフロントマターの処理"""
        md_file = Path(temp_dir) / "frontmatter.md"
        md_file.write_text("---\ntitle: Test\nauthor: Me\n---\n\n# Content")

        response = client.get("/api/file", params={"path": "frontmatter.md"})
        content = response.json()["content"]

        # YAMLがコードブロックとして表示される
        assert "language-yaml" in content

    def test_mermaid_block(self, client, temp_dir):
        """Mermaidブロックの処理"""
        md_file = Path(temp_dir) / "mermaid.md"
        md_file.write_text("```mermaid\ngraph TD\n    A --> B\n```")

        response = client.get("/api/file", params={"path": "mermaid.md"})
        content = response.json()["content"]

        assert "language-mermaid" in content

    def test_task_list(self, client, temp_dir):
        """タスクリストの変換"""
        md_file = Path(temp_dir) / "tasks.md"
        md_file.write_text("- [x] Done\n- [ ] Todo")

        response = client.get("/api/file", params={"path": "tasks.md"})
        content = response.json()["content"]

        assert 'type="checkbox"' in content


class TestFileWatcher:
    """ファイル監視のテスト"""

    def test_set_watching_file(self, temp_dir):
        """監視ファイルの設定"""
        state.set_root_path(temp_dir)
        readme = Path(temp_dir) / "README.md"

        state.set_watching_file(str(readme))

        assert state.current_watching_file == str(readme)
        assert state.last_mtime > 0

    def test_mtime_change_detection(self, temp_dir):
        """mtime変更の検出"""
        state.set_root_path(temp_dir)
        readme = Path(temp_dir) / "README.md"

        state.set_watching_file(str(readme))
        original_mtime = state.last_mtime

        # ファイルを更新
        import time
        time.sleep(0.1)  # mtimeの精度のため
        readme.write_text("# Updated content")

        new_mtime = os.path.getmtime(str(readme))
        assert new_mtime != original_mtime


class TestSecurity:
    """セキュリティテスト"""

    def test_path_traversal_dotdot(self, client):
        """パストラバーサル: ../"""
        response = client.get("/api/file", params={"path": "../secret.txt"})
        assert response.status_code in [403, 404]

    def test_path_traversal_encoded(self, client):
        """パストラバーサル: エンコードされた../"""
        response = client.get("/api/file", params={"path": "..%2F..%2Fetc%2Fpasswd"})
        assert response.status_code in [403, 404]

    def test_absolute_path(self, client):
        """絶対パスのブロック"""
        response = client.get("/api/file", params={"path": "/etc/passwd"})
        assert response.status_code in [403, 404]


class TestUploadDownload:
    """アップロード/ダウンロードのテスト"""

    def test_upload_single_file(self, client, temp_dir):
        """単一ファイルのアップロード"""
        file_content = b"test content"
        response = client.post(
            "/api/upload",
            data={"path": ""},
            files={"files": ("uploaded.txt", file_content, "text/plain")}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "uploaded.txt" in result["uploaded"]

        # ファイルが作成されたか確認
        uploaded_file = Path(temp_dir) / "uploaded.txt"
        assert uploaded_file.exists()
        assert uploaded_file.read_bytes() == file_content

    def test_upload_to_subdirectory(self, client, temp_dir):
        """サブディレクトリへのアップロード"""
        file_content = b"nested content"
        response = client.post(
            "/api/upload",
            data={"path": "subdir"},
            files={"files": ("nested_upload.txt", file_content, "text/plain")}
        )
        assert response.status_code == 200

        uploaded_file = Path(temp_dir) / "subdir" / "nested_upload.txt"
        assert uploaded_file.exists()

    def test_upload_multiple_files(self, client, temp_dir):
        """複数ファイルのアップロード"""
        response = client.post(
            "/api/upload",
            data={"path": ""},
            files=[
                ("files", ("file1.txt", b"content1", "text/plain")),
                ("files", ("file2.txt", b"content2", "text/plain"))
            ]
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result["uploaded"]) == 2

    def test_download_file(self, client, temp_dir):
        """ファイルのダウンロード"""
        response = client.get("/api/download", params={"path": "README.md"})
        assert response.status_code == 200
        assert "attachment" in response.headers.get("content-disposition", "")

    def test_download_not_found(self, client):
        """存在しないファイルのダウンロード"""
        response = client.get("/api/download", params={"path": "nonexistent.txt"})
        assert response.status_code == 404


class TestMediaEndpoints:
    """メディアエンドポイントのテスト"""

    def test_get_image(self, client, temp_dir):
        """画像ファイル取得"""
        # テスト用PNG画像を作成（最小限の有効なPNG）
        png_header = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 pixel
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        img_file = Path(temp_dir) / "test.png"
        img_file.write_bytes(png_header)

        response = client.get("/api/image", params={"path": "test.png"})
        assert response.status_code == 200
        assert "image/png" in response.headers["content-type"]

    def test_get_image_not_image(self, client, temp_dir):
        """画像でないファイルへのリクエスト"""
        response = client.get("/api/image", params={"path": "README.md"})
        assert response.status_code == 400

    def test_get_pdf(self, client, temp_dir):
        """PDFファイル取得"""
        # 最小限のPDFを作成
        pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>"
        pdf_file = Path(temp_dir) / "test.pdf"
        pdf_file.write_bytes(pdf_content)

        response = client.get("/api/pdf", params={"path": "test.pdf"})
        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]

    def test_get_pdf_not_pdf(self, client, temp_dir):
        """PDFでないファイルへのリクエスト"""
        response = client.get("/api/pdf", params={"path": "README.md"})
        assert response.status_code == 400


class TestUtilities:
    """ユーティリティ関数のテスト"""

    def test_escape_html(self):
        """HTMLエスケープ"""
        from mdv.rendering import escape_html

        assert escape_html("<script>") == "&lt;script&gt;"
        assert escape_html("a & b") == "a &amp; b"
        assert escape_html("normal") == "normal"

    def test_sanitize_filename(self):
        """ファイル名サニタイズ"""
        from mdv.path_security import sanitize_filename

        assert sanitize_filename("test.txt") == "test.txt"
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("path/to/file.txt") == "file.txt"

    def test_render_code(self):
        """コードレンダリング"""
        from mdv.rendering import render_code

        result = render_code("print('hello')", "python")
        assert "<pre>" in result
        assert "language-python" in result
        assert "print" in result

    def test_render_text(self):
        """テキストレンダリング"""
        from mdv.rendering import render_text

        result = render_text("plain text")
        assert "<pre" in result
        assert "plain-text" in result
        assert "plain text" in result


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_save_nonexistent_file(self, client, temp_dir):
        """存在しないファイルの保存"""
        response = client.post(
            "/api/file",
            json={"path": "nonexistent.md", "content": "new content"}
        )
        assert response.status_code == 404

    def test_mkdir_existing_directory(self, client, temp_dir):
        """既存ディレクトリへのmkdir"""
        response = client.post("/api/mkdir", json={"path": "subdir"})
        assert response.status_code == 400

    def test_move_to_existing_destination(self, client, temp_dir):
        """既存の移動先への移動"""
        response = client.post(
            "/api/move",
            json={"source": "README.md", "destination": "test.py"}
        )
        assert response.status_code == 400

    def test_delete_directory(self, client, temp_dir):
        """ディレクトリの削除"""
        # サブディレクトリを作成
        new_dir = Path(temp_dir) / "to_delete_dir"
        new_dir.mkdir()
        (new_dir / "file.txt").write_text("content")

        response = client.delete("/api/file", params={"path": "to_delete_dir"})
        assert response.status_code == 200
        assert not new_dir.exists()

    def test_get_file_binary_error(self, client, temp_dir):
        """バイナリファイル読み込み（.txtとしてアクセス）"""
        # バイナリファイルを.txtとして作成
        binary_file = Path(temp_dir) / "binary.txt"
        binary_file.write_bytes(bytes([0x00, 0x01, 0x02, 0xFF, 0xFE]))

        response = client.get("/api/file", params={"path": "binary.txt"})
        # UTF-8としてデコードできない場合は400エラー
        assert response.status_code == 400

    def test_validate_path_for_write(self, client, temp_dir):
        """書き込み用パス検証"""
        # 新規ファイルパスでも親ディレクトリが存在すればOK
        response = client.post("/api/mkdir", json={"path": "new_subdir/nested"})
        assert response.status_code == 200
        assert (Path(temp_dir) / "new_subdir" / "nested").exists()


class TestAppState:
    """AppState クラスのテスト"""

    def test_add_remove_client(self):
        """クライアント追加・削除"""
        from mdv.websocket_manager import WebSocketManager

        ws_manager = WebSocketManager()
        mock_client = object()

        ws_manager.add(mock_client)
        assert mock_client in ws_manager.clients

        ws_manager.remove(mock_client)
        assert mock_client not in ws_manager.clients

    def test_remove_nonexistent_client(self):
        """存在しないクライアントの削除（エラーなし）"""
        from mdv.websocket_manager import WebSocketManager

        ws_manager = WebSocketManager()
        mock_client = object()

        # 存在しないクライアントを削除してもエラーにならない
        ws_manager.remove(mock_client)
        assert mock_client not in ws_manager.clients

    def test_set_watching_file_nonexistent(self, temp_dir):
        """存在しないファイルの監視設定"""
        state.set_root_path(temp_dir)
        nonexistent = str(Path(temp_dir) / "nonexistent.md")

        state.set_watching_file(nonexistent)

        assert state.current_watching_file == nonexistent
        assert state.last_mtime == 0  # OSErrorで0にリセット
