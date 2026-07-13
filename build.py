"""MoonSpace 打包脚本。

打包前会先运行 pytest；测试失败时不生成 exe。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def run_command(command: list[str]) -> None:
    """运行子命令并在失败时终止打包流程。"""
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    """运行测试并用 PyInstaller 生成 MoonSpace.exe。"""
    run_command([sys.executable, "-m", "pytest"])

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        "MoonSpace",
        "main.py",
    ]

    separator = ";" if sys.platform.startswith("win") else ":"
    for asset_group in ("audio", "sprites"):
        source_dir = PROJECT_ROOT / "assets" / asset_group
        if source_dir.exists():
            command.extend(
                ["--add-data", f"{source_dir}{separator}assets/{asset_group}"]
            )

    run_command(command)


if __name__ == "__main__":
    main()
