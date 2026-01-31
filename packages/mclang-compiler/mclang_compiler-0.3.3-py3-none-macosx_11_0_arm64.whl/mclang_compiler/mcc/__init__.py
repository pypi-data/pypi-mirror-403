"""
MCLang Compiler - Binary Distribution

This package contains the pre-compiled mcc executable.
Version: 0.3.3
Platform: macosx_11_0_arm64
"""

__version__ = "0.3.3"

import os
import sys
from pathlib import Path

def get_executable_path():
    """获取可执行文件路径"""
    current_file = Path(__file__).resolve()
    return current_file.parent / "bin" / "mcc"

def main():
    """Entry point for console script"""
    bin_path = get_executable_path()
    if not bin_path.exists():
        print(f"Error: mcc executable not found at {bin_path}", file=sys.stderr)
        sys.exit(1)

    # 启动可执行文件
    os.execv(str(bin_path), [str(bin_path)] + sys.argv[1:])
