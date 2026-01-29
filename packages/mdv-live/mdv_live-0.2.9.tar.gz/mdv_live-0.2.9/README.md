# MDV - Markdown Viewer

ファイルツリー + ライブプレビュー + ファイルブラウザ機能付きマークダウンビューア

## Features

- 📁 左側にフォルダツリー表示
- 📄 マークダウンをHTMLでレンダリング
- 🔄 ファイル更新時に自動リロード（WebSocket）
- 🎨 シンタックスハイライト（highlight.js）
- 📊 Mermaid図のレンダリング対応
- 🌙 ダーク/ライトテーマ切り替え
- ✏️ インラインエディタ（Cmd+E）
- 📥 PDF出力（Cmd+P）
- 🎬 動画/音声プレビュー

### ファイルブラウザ機能

- 右クリックコンテキストメニュー
  - ファイル：開く、ダウンロード、名前変更、パスコピー、削除
  - フォルダ：新規フォルダ、アップロード、名前変更、パスコピー、削除
- ドラッグ&ドロップ
  - ファイル/フォルダをフォルダへ移動
  - 外部ファイルをドロップしてアップロード
- キーボードショートカット
  - Delete/Backspace：選択アイテムを削除
  - F2：名前変更

## Installation

```bash
# PyPIからインストール（推奨）
pip install mdv-live

# または開発版をインストール
git clone https://github.com/panhouse/mdv.git
cd mdv
pip install -e .
```

## Usage

```bash
# カレントディレクトリを表示
mdv

# 特定のディレクトリを表示
mdv ./project/

# 特定のファイルを開く
mdv README.md

# ポート指定
mdv -p 9000

# ブラウザを自動で開かない
mdv --no-browser

# MarkdownをPDFに変換
mdv --pdf README.md
mdv --pdf README.md -o output.pdf

# サーバー管理
mdv -l        # 稼働中のサーバー一覧
mdv -k -a     # 全サーバー停止
mdv -k <PID>  # 特定サーバー停止
```

## Keyboard Shortcuts

| ショートカット | 機能 |
|---------------|------|
| Cmd/Ctrl + B | サイドバー表示切替 |
| Cmd/Ctrl + E | 編集モード切替 |
| Cmd/Ctrl + S | 保存（編集モード時） |
| Cmd/Ctrl + P | PDF出力 |
| Cmd/Ctrl + W | タブを閉じる |
| Delete/Backspace | ファイル/フォルダ削除 |
| F2 | 名前変更 |

## Architecture

```
mdv/
├── __init__.py           # バージョン管理
├── __main__.py           # エントリポイント
├── cli.py                # CLIオプション・PDF変換
├── server.py             # FastAPIルート定義・オーケストレーション
├── models.py             # Pydanticモデル
├── file_types.py         # ファイルタイプ判定（レジストリパターン）
├── state.py              # アプリケーション状態管理
├── websocket_manager.py  # WebSocket接続管理
├── rendering.py          # Markdown/コードレンダリング
├── file_tree.py          # ファイルツリー構築
├── path_security.py      # パス検証・セキュリティ
├── file_response.py      # APIレスポンス生成
├── media_streaming.py    # メディアストリーミング（Range対応）
├── watcher.py            # ファイル監視（ポーリング）
└── static/
    ├── index.html        # HTMLテンプレート
    ├── styles.css        # CSSスタイル
    └── app.js            # JavaScriptアプリ
```

## Requirements

- Python 3.9+
- FastAPI
- uvicorn
- markdown-it-py
- python-multipart

## Advanced: macOS Finder Integration

macOSで`.md`ファイルをダブルクリックしてMDVで開けるようにする設定です。

### セットアップスクリプトを使用（推奨）

```bash
# mdvがインストールされていることを確認
which mdv

# セットアップスクリプトを実行
curl -fsSL https://raw.githubusercontent.com/panhouse/mdv/main/scripts/setup-macos-app.sh | bash
```

または、リポジトリをクローンしている場合：

```bash
./scripts/setup-macos-app.sh
```

### 手動セットアップ

<details>
<summary>クリックして展開</summary>

1. mdvのパスを確認：
```bash
which mdv
# 例: /usr/local/bin/mdv
```

2. AppleScriptファイルを作成（`~/MDV.applescript`）：
```applescript
on open theFiles
    repeat with theFile in theFiles
        set filePath to POSIX path of theFile
        -- ↓ 自分のmdvパスに置き換える
        do shell script "nohup /usr/local/bin/mdv " & quoted form of filePath & " > /dev/null 2>&1 &"
    end repeat
end open

on run
    display dialog "MDV Markdown Viewer" buttons {"OK"} default button "OK"
end run
```

3. アプリにコンパイル：
```bash
osacompile -o /tmp/MDV.app ~/MDV.applescript
```

4. Info.plistを設定（`/tmp/MDV.app/Contents/Info.plist`）：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.mdv.viewer</string>
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeName</key>
            <string>Markdown Document</string>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
            <key>LSItemContentTypes</key>
            <array>
                <string>net.daringfireball.markdown</string>
            </array>
            <key>CFBundleTypeExtensions</key>
            <array>
                <string>md</string>
                <string>markdown</string>
            </array>
        </dict>
    </array>
    <key>CFBundleExecutable</key>
    <string>droplet</string>
    <key>CFBundleName</key>
    <string>MDV</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
</dict>
</plist>
```

5. 署名してインストール：
```bash
codesign --force --deep --sign - /tmp/MDV.app
sudo mv /tmp/MDV.app /Applications/
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f /Applications/MDV.app
```

</details>

### デフォルトアプリに設定

1. Finderで任意の`.md`ファイルを右クリック
2. 「情報を見る」を選択
3. 「このアプリケーションで開く」で「MDV」を選択
4. 「すべてを変更...」をクリック
