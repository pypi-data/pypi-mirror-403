"""
ML-Easy-Setup SDK (mles)

一行代码实现深度学习模型构建与训练

设计理念:
- Human-Centric API: 专注于研究问题，而非框架细节
- Convention over Configuration: 合理的默认值
- Full PyTorch Compatibility: 与原生代码无缝协作

核心模块:
    SimpleModel: 通过层大小列表构建神经网络
    AutoTrainer: 自动化训练循环
    get_device: 自动检测最佳计算设备
    magic: 极致 one-liner API（推荐！）

示例:
    >>> from ml_easy_setup.sdk import SimpleModel, AutoTrainer
    >>>
    >>> # 1. 创建模型
    >>> model = SimpleModel([784, 128, 10], task='classification')
    >>>
    >>> # 2. 训练模型
    >>> trainer = AutoTrainer()
    >>> history = trainer.fit(model, train_loader, epochs=50)

Magic API (推荐):
    >>> from ml_easy_setup.sdk.magic import train, predict
    >>>
    >>> # 一行代码完成训练
    >>> result = train("data.csv", target="label", epochs=100)
    >>> print(f"Accuracy: {result.metrics['accuracy']:.2%}")
    >>>
    >>> # 一行代码预测
    >>> predictions = predict(result.model, "test.csv")
"""

# 版本信息
__version__ = "0.1.0"

# ========================================================================
# 核心模型 API
# ========================================================================
from .models import (
    SimpleModel,
    SequentialBuilder,
    mlp,
    MLPFactory,
)

# ========================================================================
# 核心训练器 API
# ========================================================================
from .trainers import (
    AutoTrainer,
    TrainerConfig,
    TrainingHistory,
    fit,
    accuracy_score,
)

# ========================================================================
# 设备管理 API
# ========================================================================
from .utils import (
    get_device,
    detect_device,
    get_device_info,
    print_device_info,
    DeviceContext,
    auto_device,
)

# ========================================================================
# 类型定义 API
# ========================================================================
from .utils.types import (
    TaskType,
    ActivationType,
    OptimizerType,
    LossType,
    DeviceType,
    get_activation,
    create_loss,
    create_optimizer,
)

# ========================================================================
# Magic API - 极致 one-liner
# ========================================================================
try:
    from .magic import (
        train,
        predict,
        tabular_classifier,
        regressor,
        binary_classifier,
        TrainResult,
    )
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

# ========================================================================
# 公开 API
# ========================================================================
__all__ = [
    # 版本
    "__version__",
    # 模型
    "SimpleModel",
    "SequentialBuilder",
    "mlp",
    "MLPFactory",
    # 训练器
    "AutoTrainer",
    "TrainerConfig",
    "TrainingHistory",
    "fit",
    "accuracy_score",
    # 设备
    "get_device",
    "detect_device",
    "get_device_info",
    "print_device_info",
    "DeviceContext",
    "auto_device",
    # 类型
    "TaskType",
    "ActivationType",
    "OptimizerType",
    "LossType",
    "DeviceType",
    "get_activation",
    "create_loss",
    "create_optimizer",
]

# Magic API（如果可用）
if MAGIC_AVAILABLE:
    __all__.extend([
        "train",
        "predict",
        "tabular_classifier",
        "regressor",
        "binary_classifier",
        "TrainResult",
    ])

# ========================================================================
# 便捷导入别名
# ========================================================================
# 常用别名，提高 API 友好度
Model = SimpleModel  # 更短的别名
Trainer = AutoTrainer  # 更短的别名


def __getattr__(name: str):
    """支持便捷别名"""
    if name == "Model":
        return SimpleModel
    if name == "Trainer":
        return AutoTrainer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
