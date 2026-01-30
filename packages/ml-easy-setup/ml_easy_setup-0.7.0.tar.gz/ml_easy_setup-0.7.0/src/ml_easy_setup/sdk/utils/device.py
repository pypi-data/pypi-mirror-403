"""
设备管理模块 - 自动检测并选择最佳计算设备

设计理念:
- 自动检测可用的 GPU (CUDA/MPS)
- 提供统一的设备接口
- 支持设备亲和性配置
- 优雅降级：GPU 不可用时自动使用 CPU
"""

from __future__ import annotations

import platform
from typing import Literal, Optional
import torch

from .types import DeviceType


# ========================================================================
# 全局设备缓存
# ========================================================================
_cached_device: Optional[torch.device] = None
_device_info: dict[str, str] = {}


# ========================================================================
# 设备检测与选择
# ========================================================================
def detect_device() -> torch.device:
    """
    自动检测并返回最佳可用设备

    检测优先级:
    1. CUDA (NVIDIA GPU) - 最高性能
    2. MPS (Apple Silicon) - M1/M2/M3 芯片
    3. CPU - 通用后备方案

    Returns:
        检测到的最佳 torch.device

    Examples:
        >>> device = detect_device()
        >>> model.to(device)
    """
    global _cached_device, _device_info

    if _cached_device is not None:
        return _cached_device

    # 1. 检测 CUDA (NVIDIA GPU)
    if torch.cuda.is_available():
        _cached_device = torch.device("cuda")
        _device_info = {
            "type": "cuda",
            "name": torch.cuda.get_device_name(0),
            "count": torch.cuda.device_count(),
            "capability": f"{torch.cuda.get_device_capability(0)[0]}.{torch.cuda.get_device_capability(0)[1]}",
        }
        return _cached_device

    # 2. 检测 MPS (Apple Silicon)
    if torch.backends.mps.is_available():
        _cached_device = torch.device("mps")
        _device_info = {
            "type": "mps",
            "name": "Apple Silicon GPU",
            "platform": platform.mac_ver()[0],
        }
        return _cached_device

    # 3. 默认 CPU
    _cached_device = torch.device("cpu")
    _device_info = {
        "type": "cpu",
        "name": platform.processor(),
    }
    return _cached_device


def get_device(device: DeviceType = "auto") -> torch.device:
    """
    获取指定设备或自动检测最佳设备

    Args:
        device: 设备类型
            - 'auto': 自动检测最佳设备（默认）
            - 'cuda': 强制使用 CUDA
            - 'mps': 强制使用 MPS
            - 'cpu': 强制使用 CPU

    Returns:
        torch.device 实例

    Raises:
        ValueError: 当请求的设备不可用时

    Examples:
        >>> device = get_device()  # 自动检测
        >>> device = get_device("cuda")  # 强制 CUDA
        >>> device = get_device("cpu")  # 强制 CPU
    """
    if device == "auto":
        return detect_device()

    if device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is not available. "
                "Please install PyTorch with CUDA support or use device='auto'."
            )
        return torch.device("cuda")

    if device == "mps":
        if not torch.backends.mps.is_available():
            raise RuntimeError(
                "MPS is not available. "
                "MPS is only supported on Apple Silicon (M1/M2/M3) Macs."
            )
        return torch.device("mps")

    if device == "cpu":
        return torch.device("cpu")

    raise ValueError(
        f"Invalid device type: '{device}'. "
        f"Choose from: 'auto', 'cuda', 'mps', 'cpu'."
    )


def get_device_info() -> dict[str, str]:
    """
    获取当前设备的详细信息

    Returns:
        包含设备信息的字典

    Examples:
        >>> info = get_device_info()
        >>> print(f"Using: {info['name']}")
    """
    if _cached_device is None:
        detect_device()
    return _device_info.copy()


def clear_device_cache() -> None:
    """
    清除设备缓存

    用于测试或重新检测设备
    """
    global _cached_device, _device_info
    _cached_device = None
    _device_info = {}


# ========================================================================
# 设备相关工具函数
# ========================================================================
def device_count(device_type: Literal["cuda", "mps"] = "cuda") -> int:
    """
    获取指定类型的设备数量

    Args:
        device_type: 设备类型 ('cuda' 或 'mps')

    Returns:
        可用设备数量
    """
    if device_type == "cuda":
        return torch.cuda.device_count() if torch.cuda.is_available() else 0
    if device_type == "mps":
        return 1 if torch.backends.mps.is_available() else 0
    return 0


def set_device(device: torch.device | str) -> None:
    """
    设置当前设备（对 CUDA 多 GPU 有用）

    Args:
        device: 目标设备
    """
    if isinstance(device, str):
        device = torch.device(device)

    if device.type == "cuda":
        torch.cuda.set_device(device)
    # MPS 和 CPU 不需要设置当前设备


def current_device() -> torch.device:
    """
    获取当前设备

    Returns:
        当前 torch.device
    """
    if torch.cuda.is_available():
        return torch.device(f"cuda:{torch.cuda.current_device()}")
    return detect_device()


def synchronize(device: torch.device | str | None = None) -> None:
    """
    同步设备操作（用于精确计时）

    Args:
        device: 要同步的设备，None 表示使用当前设备
    """
    if device is None:
        device = detect_device()
    elif isinstance(device, str):
        device = torch.device(device)

    if device.type == "cuda":
        torch.cuda.synchronize(device)
    elif device.type == "mps":
        torch.mps.synchronize(device)
    # CPU 不需要同步


# ========================================================================
# 内存管理
# ========================================================================
def get_memory_usage(device: torch.device | str | None = None) -> dict[str, float]:
    """
    获取设备内存使用情况（仅支持 CUDA）

    Args:
        device: 目标设备

    Returns:
        包含内存信息的字典（单位：GB）
    """
    if device is None:
        device = detect_device()
    elif isinstance(device, str):
        device = torch.device(device)

    if device.type != "cuda":
        return {"total": 0.0, "used": 0.0, "free": 0.0}

    allocated = torch.cuda.memory_allocated(device) / 1024**3
    reserved = torch.cuda.memory_reserved(device) / 1024**3
    total = torch.cuda.get_device_properties(device).total_memory / 1024**3

    return {
        "total": total,
        "used": allocated,
        "reserved": reserved,
        "free": total - allocated,
    }


def empty_cache(device: torch.device | str | None = None) -> None:
    """
    释放设备缓存（仅支持 CUDA）

    Args:
        device: 目标设备
    """
    if device is None:
        device = detect_device()
    elif isinstance(device, str):
        device = torch.device(device)

    if device.type == "cuda":
        torch.cuda.empty_cache()


# ========================================================================
# 上下文管理器
# ========================================================================
class DeviceContext:
    """
    设备上下文管理器

    自动处理张量的设备转移

    Examples:
        >>> with DeviceContext("cuda"):
        ...     model = SimpleModel([784, 128, 10])
        ...     # model 自动在 cuda 上
    """

    def __init__(self, device: DeviceType = "auto"):
        self.device = get_device(device)
        self.original_device = None

    def __enter__(self) -> "DeviceContext":
        self.original_device = current_device()
        set_device(self.device)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.original_device is not None:
            set_device(self.original_device)


# ========================================================================
# 装饰器
# ========================================================================
def auto_device(func):
    """
    装饰器：自动将模型转移到检测到的最佳设备

    Examples:
        >>> @auto_device
        ... def create_model():
        ...     return SimpleModel([784, 128, 10])
        >>> model = create_model()  # 自动在最佳设备上
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        device = detect_device()
        if hasattr(result, "to"):
            return result.to(device)
        return result
    return wrapper


# ========================================================================
# 打印设备信息
# ========================================================================
def print_device_info() -> None:
    """
    打印格式化的设备信息

    Examples:
        >>> print_device_info()
        ╔════════════════════════════════════════╗
        ║           Device Information           ║
        ╠════════════════════════════════════════╣
        ║ Type:  CUDA                           ║
        ║ Name:  NVIDIA GeForce RTX 3090        ║
        ║ Count: 1                              ║
        ╚════════════════════════════════════════╝
    """
    info = get_device_info()
    device_type = info.get("type", "unknown").upper()

    lines = [
        "╔════════════════════════════════════════╗",
        "║           Device Information           ║",
        "╠════════════════════════════════════════╣",
        f"║ Type:  {device_type:<29} ║",
    ]

    if "name" in info:
        name = info["name"][:29]
        lines.append(f"║ Name:  {name:<29} ║")

    if "count" in info:
        lines.append(f"║ Count: {info['count']:<29} ║")

    if "capability" in info:
        lines.append(f"║ Compute: {info['capability']:<27} ║")

    lines.append("╚════════════════════════════════════════╝")

    print("\n".join(lines))
