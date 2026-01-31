"""
Markdown / Code / Text レンダリング機能

SRP: レンダリングのみを担当
"""

from __future__ import annotations

import re
from typing import Optional

from markdown_it import MarkdownIt
from mdit_py_plugins.tasklists import tasklists_plugin

from .file_types import FileTypeInfo


# === HTML Utilities ===

def escape_html(text: str) -> str:
    """HTMLエスケープ（XSS対策）"""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


# === Markdown Preprocessing ===

# YAMLフロントマターのパターン（ファイル先頭の---で囲まれた部分）
_FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*(\n|$)', re.DOTALL)

# 見出し後のYAMLメタデータブロック（---で囲まれたkey: value形式）
_YAML_BLOCK_PATTERN = re.compile(
    r'(^|\n)(#{1,6}\s+[^\n]+)\n+---\s*\n((?:[a-zA-Z_][a-zA-Z0-9_]*:\s*[^\n]*\n?)+)---\s*(\n|$)',
    re.MULTILINE
)

# Mermaidコードブロックのパターン
_MERMAID_PATTERN = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)


def _convert_frontmatter_to_codeblock(content: str) -> str:
    """YAMLフロントマターをコードブロックに変換"""
    match = _FRONTMATTER_PATTERN.match(content)
    if match:
        frontmatter_content = match.group(1)
        rest_of_content = content[match.end():]
        return f"```yaml\n{frontmatter_content}\n```\n{rest_of_content}"
    return content


def _convert_yaml_blocks_to_codeblocks(content: str) -> str:
    """見出し後のYAMLメタデータブロックをコードブロックに変換"""
    def replace_yaml_block(match: re.Match) -> str:
        prefix = match.group(1)
        heading = match.group(2)
        yaml_content = match.group(3).rstrip('\n')
        suffix = match.group(4)
        return f"{prefix}{heading}\n\n```yaml\n{yaml_content}\n```{suffix}"

    return _YAML_BLOCK_PATTERN.sub(replace_yaml_block, content)


def _protect_mermaid_blocks(content: str) -> tuple[str, list[str]]:
    """Mermaidコードブロックをプレースホルダで保護"""
    mermaid_blocks: list[str] = []

    def replace_mermaid(match: re.Match) -> str:
        mermaid_blocks.append(match.group(1))
        return f"<!--MERMAID_PLACEHOLDER_{len(mermaid_blocks) - 1}-->"

    protected_content = _MERMAID_PATTERN.sub(replace_mermaid, content)
    return protected_content, mermaid_blocks


def _restore_mermaid_blocks(html: str, mermaid_blocks: list[str]) -> str:
    """Mermaidコードブロックを復元"""
    for i, mermaid_code in enumerate(mermaid_blocks):
        placeholder = f"<!--MERMAID_PLACEHOLDER_{i}-->"
        escaped_code = escape_html(mermaid_code)
        mermaid_html = f'<pre><code class="language-mermaid">{escaped_code}</code></pre>'
        html = html.replace(f"<p>{placeholder}</p>", mermaid_html)
        html = html.replace(placeholder, mermaid_html)
    return html


# === Markdown Parser (Singleton) ===

_md_parser: Optional[MarkdownIt] = None


def _get_md_parser() -> MarkdownIt:
    """markdown-it-pyパーサーを取得（遅延初期化）"""
    global _md_parser
    if _md_parser is None:
        _md_parser = MarkdownIt("commonmark", {"html": True, "typographer": True, "breaks": True})
        _md_parser.enable("table")
        _md_parser.enable("strikethrough")
        _md_parser.use(tasklists_plugin)
    return _md_parser


# === Public Rendering Functions ===

def render_markdown(content: str) -> str:
    """マークダウンをHTMLに変換"""
    # 前処理
    content = _convert_frontmatter_to_codeblock(content)
    content = _convert_yaml_blocks_to_codeblocks(content)
    content, mermaid_blocks = _protect_mermaid_blocks(content)

    # パース＆レンダリング
    md = _get_md_parser()
    tokens = md.parse(content)

    # data-line属性を追加
    for token in tokens:
        if token.map and len(token.map) >= 1:
            if token.attrs is None:
                token.attrs = {}
            token.attrs["data-line"] = str(token.map[0])

    html = md.renderer.render(tokens, md.options, {})

    # 後処理
    return _restore_mermaid_blocks(html, mermaid_blocks)


def render_code(content: str, lang: Optional[str] = None) -> str:
    """コードをシンタックスハイライト用HTMLに変換"""
    escaped = escape_html(content)
    lang_class = f"language-{lang}" if lang else ""
    return f'<pre><code class="{lang_class}">{escaped}</code></pre>'


def render_text(content: str) -> str:
    """プレーンテキストをHTMLに変換"""
    escaped = escape_html(content)
    return f'<pre class="plain-text">{escaped}</pre>'


def render_file_content(content: str, file_info: FileTypeInfo) -> str:
    """ファイルタイプに応じてコンテンツをレンダリング"""
    if file_info.type == "markdown":
        return render_markdown(content)
    if file_info.type == "code":
        return render_code(content, file_info.lang)
    return render_text(content)
