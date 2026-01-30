"""
ML Easy Setup - 一键配置机器学习/深度学习环境

解决依赖冲突和配置难题，让科研工作更专注于算法本身。
"""

__version__ = "0.5.0"

from ml_easy_setup.core.env_manager import EnvironmentManager
from ml_easy_setup.core.template import TemplateManager

# SDK 模块 - Python API for model development
from ml_easy_setup.sdk import (
    # 模型
    SimpleModel,
    SequentialBuilder,
    mlp,
    MLPFactory,
    # 训练器
    AutoTrainer,
    TrainerConfig,
    TrainingHistory,
    fit,
    accuracy_score,
    # 设备管理
    get_device,
    detect_device,
    print_device_info,
    # 类型定义
    TaskType,
    ActivationType,
    OptimizerType,
    LossType,
)

__all__ = [
    # 核心模块
    "EnvironmentManager",
    "TemplateManager",
    "__version__",
    # SDK 模型
    "SimpleModel",
    "SequentialBuilder",
    "mlp",
    "MLPFactory",
    # SDK 训练器
    "AutoTrainer",
    "TrainerConfig",
    "TrainingHistory",
    "fit",
    "accuracy_score",
    # SDK 设备管理
    "get_device",
    "detect_device",
    "print_device_info",
    # SDK 类型定义
    "TaskType",
    "ActivationType",
    "OptimizerType",
    "LossType",
]
