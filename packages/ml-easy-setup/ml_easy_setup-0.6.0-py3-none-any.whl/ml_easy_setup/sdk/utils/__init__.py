"""SDK 工具模块"""

from .types import (
    TaskType,
    ActivationType,
    OptimizerType,
    LossType,
    DeviceType,
    get_activation,
    get_default_loss,
    create_loss,
    create_optimizer,
)

from .device import (
    detect_device,
    get_device,
    get_device_info,
    clear_device_cache,
    device_count,
    set_device,
    current_device,
    synchronize,
    get_memory_usage,
    empty_cache,
    DeviceContext,
    auto_device,
    print_device_info,
)

__all__ = [
    # 类型
    "TaskType",
    "ActivationType",
    "OptimizerType",
    "LossType",
    "DeviceType",
    # 类型工具
    "get_activation",
    "get_default_loss",
    "create_loss",
    "create_optimizer",
    # 设备
    "detect_device",
    "get_device",
    "get_device_info",
    "clear_device_cache",
    "device_count",
    "set_device",
    "current_device",
    "synchronize",
    "get_memory_usage",
    "empty_cache",
    "DeviceContext",
    "auto_device",
    "print_device_info",
]
