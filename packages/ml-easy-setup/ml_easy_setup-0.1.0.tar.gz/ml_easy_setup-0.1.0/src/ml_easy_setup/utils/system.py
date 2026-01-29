"""
系统工具函数
"""

import subprocess
import sys
from typing import Optional


def get_python_version() -> str:
    """
    获取当前 Python 版本

    Returns:
        版本字符串 (如 "3.10.0")
    """
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def check_command_exists(command: str) -> bool:
    """
    检查命令是否存在

    Args:
        command: 命令名称

    Returns:
        命令是否存在
    """
    try:
        subprocess.run(
            [command, "--version"],
            capture_output=True,
            timeout=2
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_command(
    command: list[str],
    cwd: Optional[str] = None,
    check: bool = True,
    capture: bool = True
) -> subprocess.CompletedProcess:
    """
    运行命令

    Args:
        command: 命令列表
        cwd: 工作目录
        check: 是否检查返回码
        capture: 是否捕获输出

    Returns:
        命令执行结果
    """
    kwargs = {"cwd": cwd, "check": check}
    if capture:
        kwargs["capture_output"] = True
        kwargs["text"] = True

    return subprocess.run(command, **kwargs)


def get_platform() -> str:
    """
    获取当前平台

    Returns:
        平台字符串 (linux, darwin, windows)
    """
    return sys.platform
