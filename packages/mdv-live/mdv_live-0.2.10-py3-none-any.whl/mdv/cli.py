#!/usr/bin/env python3
"""
MDV - Markdown Viewer CLI
どこからでも呼び出せるマークダウンビューア
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


# === Process Management (SRP: プロセス管理の責任) ===


@dataclass
class ProcessInfo:
    """プロセス情報"""
    pid: str
    port: str
    command: str


class ProcessManager:
    """MDVプロセスの検索・停止を担当（SRP）"""

    @staticmethod
    def get_mdv_processes() -> list[ProcessInfo]:
        """稼働中のMDVサーバープロセスを取得"""
        result = subprocess.run(
            ["lsof", "-i", "-P", "-n"],
            capture_output=True,
            text=True,
        )

        processes = []
        for line in result.stdout.strip().split("\n"):
            if "python" not in line.lower() or "LISTEN" not in line:
                continue

            parts = line.split()
            if len(parts) < 9:
                continue

            pid = parts[1]
            process_info = ProcessManager._get_process_info(pid, parts)
            if process_info:
                processes.append(process_info)

        return processes

    @staticmethod
    def _get_process_info(pid: str, parts: list[str]) -> ProcessInfo | None:
        """PIDからMDVプロセス情報を取得"""
        cmd_result = subprocess.run(
            ["ps", "-p", pid, "-o", "command="],
            capture_output=True,
            text=True,
        )
        cmd = cmd_result.stdout.strip()

        if "mdv" not in cmd.lower():
            return None

        port = ProcessManager._extract_port(parts)
        display_cmd = cmd[:80] + "..." if len(cmd) > 80 else cmd

        return ProcessInfo(pid=pid, port=port, command=display_cmd)

    @staticmethod
    def _extract_port(parts: list[str]) -> str:
        """lsof出力からポート番号を抽出"""
        port_info = parts[8] if len(parts) > 8 else ""
        if ":" in port_info:
            return port_info.split(":")[-1].split("->")[0]
        return ""

    @staticmethod
    def kill_process(pid: str) -> bool:
        """指定PIDのプロセスを停止（成功時True）"""
        result = subprocess.run(["kill", pid], capture_output=True)
        return result.returncode == 0


# === Server Commands (SRP: サーバー操作コマンドの責任) ===


def list_servers() -> int:
    """稼働中のMDVサーバーを一覧表示"""
    processes = ProcessManager.get_mdv_processes()

    if not processes:
        print("稼働中のMDVサーバーはありません")
        return 0

    print(f"稼働中のMDVサーバー: {len(processes)}件")
    print("-" * 60)
    print(f"{'PID':<8} {'Port':<8} {'Command'}")
    print("-" * 60)

    for proc in processes:
        print(f"{proc.pid:<8} {proc.port:<8} {proc.command}")

    print("-" * 60)
    print("\n停止: mdv -k -a (全停止) / mdv -k <PID> (個別停止)")
    return 0


def kill_servers(target: str | None = None, kill_all: bool = False) -> int:
    """MDVサーバーを停止"""
    if target:
        return _kill_single_server(target)

    if not kill_all:
        print("全サーバーを停止するには -a オプションが必要です")
        print("   mdv -k -a     全サーバーを停止")
        print("   mdv -k <PID>  特定のサーバーを停止")
        return 1

    return _kill_all_servers()


def _kill_single_server(pid: str) -> int:
    """特定のPIDのサーバーを停止"""
    if ProcessManager.kill_process(pid):
        print(f"PID {pid} を停止しました")
        return 0
    print(f"PID {pid} の停止に失敗しました")
    return 1


def _kill_all_servers() -> int:
    """全サーバーを停止"""
    processes = ProcessManager.get_mdv_processes()

    if not processes:
        print("稼働中のMDVサーバーはありません")
        return 0

    print(f"{len(processes)}件のMDVサーバーを停止します...")

    killed = sum(1 for proc in processes if _kill_process_with_log(proc))

    print(f"\n完了: {killed}/{len(processes)} 件を停止しました")
    return 0 if killed == len(processes) else 1


def _kill_process_with_log(proc: ProcessInfo) -> bool:
    """プロセスを停止してログ出力（成功時True）"""
    if ProcessManager.kill_process(proc.pid):
        print(f"  PID {proc.pid} (port {proc.port}) を停止")
        return True
    print(f"  PID {proc.pid} の停止に失敗")
    return False


# === PDF Conversion (SRP: PDF変換の責任) ===


_NPX_INSTALL_MESSAGE = (
    "Error: npx (Node.js) is required for PDF conversion\n"
    "Install Node.js: https://nodejs.org/"
)


def _validate_markdown_file(input_path: Path) -> str | None:
    """マークダウンファイルを検証（エラー時はエラーメッセージを返す）"""
    if not input_path.exists():
        return f"Error: File not found: {input_path}"
    if not input_path.is_file():
        return f"Error: Not a file: {input_path}"
    if input_path.suffix.lower() not in [".md", ".markdown"]:
        return f"Error: Not a markdown file: {input_path}"
    return None


def _run_md_to_pdf(input_path: Path) -> tuple[bool, str]:
    """md-to-pdfを実行（成功, エラーメッセージ）"""
    cmd = ["npx", "md-to-pdf", str(input_path)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(input_path.parent),
    )

    if result.returncode != 0:
        if "not found" in result.stderr:
            return False, _NPX_INSTALL_MESSAGE
        return False, f"Error: {result.stderr}"

    return True, ""


def _move_pdf_if_needed(default_output: Path, output_path: Path | None) -> int:
    """必要に応じてPDFを移動"""
    if output_path and output_path != default_output:
        if not default_output.exists():
            print(f"Warning: Expected PDF not found at {default_output}")
            return 1
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(default_output), str(output_path))
        print(f"PDF saved: {output_path}")
    else:
        print(f"PDF saved: {default_output}")
    return 0


def convert_to_pdf(input_path: Path, output_path: Path | None = None) -> int:
    """MarkdownファイルをPDFに変換（md-to-pdfを使用）"""
    validation_error = _validate_markdown_file(input_path)
    if validation_error:
        print(validation_error)
        return 1

    success, error_message = _run_md_to_pdf(input_path)
    if not success:
        print(error_message)
        return 1

    default_output = input_path.with_suffix(".pdf")
    return _move_pdf_if_needed(default_output, output_path)


def start_viewer(
    path: str = ".",
    port: int = 8642,
    open_browser: bool = True,
) -> None:
    """MDVサーバーを起動"""
    target_path = Path(path).resolve()

    if not target_path.exists():
        print(f"Error: Path does not exist: {target_path}")
        sys.exit(1)

    # ファイルが指定された場合、親ディレクトリをルートにして、そのファイルを開く
    initial_file: str | None = None
    if target_path.is_file():
        initial_file = target_path.name
        target_path = target_path.parent

    from .server import start_server

    start_server(
        root_path=str(target_path),
        port=port,
        open_browser=open_browser,
        initial_file=initial_file,
    )


def create_parser() -> argparse.ArgumentParser:
    """引数パーサーを作成"""
    parser = argparse.ArgumentParser(
        prog="mdv",
        description="MDV - Markdown Viewer with file tree + live preview",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mdv                    Start viewer in current directory
  mdv /path/to/dir       Start viewer in specified directory
  mdv README.md          Open specific file
  mdv --pdf README.md    Convert markdown to PDF
  mdv -p 3000            Start on port 3000
  mdv -l                 List running servers
  mdv -k -a              Stop all servers
""",
    )

    # サーバー管理オプション
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List running MDV servers",
    )
    parser.add_argument(
        "-k", "--kill",
        nargs="?",
        const="__no_pid__",
        metavar="PID",
        help="Stop server (-k -a for all, -k <PID> for specific)",
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Use with -k to stop all servers",
    )

    # ビューア起動オプション
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory or file path to view (default: current directory)",
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8642,
        help="Server port (default: 8642)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically",
    )

    # PDF変換オプション
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Convert markdown file to PDF",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        metavar="FILE",
        help="Output PDF file path (default: same name as input with .pdf extension)",
    )

    return parser


def _dispatch_command(args: argparse.Namespace) -> int | None:
    """コマンドをディスパッチ（終了コードを返す、Noneはビューア起動）"""
    if args.list:
        return list_servers()

    if args.kill is not None:
        target = args.kill if args.kill != "__no_pid__" else None
        return kill_servers(target=target, kill_all=args.all)

    if args.pdf:
        input_path = Path(args.path).resolve()
        output_path = Path(args.output).resolve() if args.output else None
        return convert_to_pdf(input_path, output_path)

    return None


def main() -> None:
    """メインエントリーポイント"""
    parser = create_parser()
    args = parser.parse_args()

    exit_code = _dispatch_command(args)
    if exit_code is not None:
        sys.exit(exit_code)

    # デフォルト: ビューア起動
    start_viewer(args.path, args.port, not args.no_browser)


if __name__ == "__main__":
    main()
