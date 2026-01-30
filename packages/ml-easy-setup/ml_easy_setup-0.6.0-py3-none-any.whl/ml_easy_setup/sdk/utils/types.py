"""
类型定义和常量配置

设计理念:
- 使用 Literal 类型约束任务类型和激活函数，提供 IDE 自动补全
- 将配置集中管理，便于未来扩展
- 使用 TypedDict 增强代码可读性和类型安全
"""

from typing import Literal, Union, Optional, Callable, TypeAlias
from enum import Enum
import torch
import torch.nn as nn


# ========================================================================
# 任务类型定义
# ========================================================================
TaskType: TypeAlias = Literal[
    "classification",  # 分类任务
    "binary",          # 二分类任务
    "regression",      # 回归任务
    "multilabel",      # 多标签分类
]


# ========================================================================
# 激活函数类型
# ========================================================================
ActivationType: TypeAlias = Literal[
    "relu",      # ReLU - 最常用
    "gelu",      # GELU - Transformer 默认
    "selu",      # SELU - 自归一化
    "tanh",      # Tanh - 传统 RNN
    "sigmoid",   # Sigmoid - 输出层常用
    "softmax",   # Softmax - 多分类输出
    "leaky_relu",# LeakyReLU - 解决死亡 ReLU
    "silu",      # SiLU (Swish) - 现代激活函数
    "none",      # 无激活函数
]


# ========================================================================
# 优化器类型
# ========================================================================
OptimizerType: TypeAlias = Literal[
    "adam",      # Adam - 通用首选
    "adamw",     # AdamW - 带权重衰减
    "sgd",       # SGD - 带动量的 SGD
    "rmsprop",   # RMSprop - RNN 传统选择
    "adagrad",   # Adagrad - 稀疏梯度
]


# ========================================================================
# 损失函数类型
# ========================================================================
LossType: TypeAlias = Literal[
    # 分类任务
    "cross_entropy",    # 交叉熵 - 多分类
    "nll",              # 负对数似然
    "hinge",            # Hinge 损失 - SVM
    # 二分类
    "bce",              # 二元交叉熵
    # 回归任务
    "mse",              # 均方误差
    "mae",              # 平均绝对误差
    "smooth_l1",        # Smooth L1 - Fast R-CNN
    "huber",            # Huber 损失 - 同 smooth_l1
    # 多标签
    "bce_with_logits",  # 带 logits 的 BCE
    # 其他
    "kl_div",           # KL 散度
    "ctc",              # CTC 损失 - 序列标注
]


# ========================================================================
# 设备类型
# ========================================================================
DeviceType: TypeAlias = Literal["auto", "cuda", "mps", "cpu"]


# ========================================================================
# 激活函数映射字典
# ========================================================================
ACTIVATION_MAP: dict[ActivationType, type[nn.Module]] = {
    "relu": nn.ReLU,
    "gelu": nn.GELU,
    "selu": nn.SELU,
    "tanh": nn.Tanh,
    "sigmoid": nn.Sigmoid,
    "softmax": nn.Softmax,
    "leaky_relu": nn.LeakyReLU,
    "silu": nn.SiLU,
    "none": nn.Identity,
}


def get_activation(activation: ActivationType, **kwargs) -> nn.Module:
    """
    获取激活函数模块

    Args:
        activation: 激活函数类型
        **kwargs: 传递给激活函数的额外参数

    Returns:
        对应的 PyTorch 激活函数模块

    Examples:
        >>> get_activation("relu")
        ReLU()
        >>> get_activation("leaky_relu", negative_slope=0.1)
        LeakyReLU(negative_slope=0.1)
    """
    if activation == "none":
        return nn.Identity()
    activation_cls = ACTIVATION_MAP.get(activation)
    if activation_cls is None:
        raise ValueError(
            f"Unsupported activation: {activation}. "
            f"Choose from {list(ACTIVATION_MAP.keys())}"
        )
    # 特殊处理 softmax，默认 dim=1
    if activation == "softmax":
        kwargs.setdefault("dim", 1)
    return activation_cls(**kwargs)


# ========================================================================
# 任务类型到损失函数的默认映射
# ========================================================================
DEFAULT_LOSS_MAP: dict[TaskType, LossType] = {
    "classification": "cross_entropy",
    "binary": "bce",
    "regression": "mse",
    "multilabel": "bce_with_logits",
}


def get_default_loss(task: TaskType) -> LossType:
    """
    根据任务类型获取默认损失函数

    Args:
        task: 任务类型

    Returns:
        对应的默认损失函数类型
    """
    loss = DEFAULT_LOSS_MAP.get(task)
    if loss is None:
        raise ValueError(f"Unsupported task type: {task}")
    return loss


# ========================================================================
# 损失函数工厂
# ========================================================================
def create_loss(loss_type: LossType, **kwargs) -> nn.Module:
    """
    创建损失函数实例

    Args:
        loss_type: 损失函数类型
        **kwargs: 传递给损失函数的额外参数

    Returns:
        PyTorch 损失函数模块

    Examples:
        >>> create_loss("mse")
        MSELoss()
        >>> create_loss("cross_entropy", label_smoothing=0.1)
        CrossEntropyLoss(label_smoothing=0.1)
    """
    loss_map: dict[LossType, Callable[[], nn.Module]] = {
        # 分类
        "cross_entropy": lambda: nn.CrossEntropyLoss(**kwargs),
        "nll": lambda: nn.NLLLoss(**kwargs),
        "hinge": lambda: nn.HingeEmbeddingLoss(**kwargs),
        # 二分类
        "bce": lambda: nn.BCELoss(**kwargs),
        # 回归
        "mse": lambda: nn.MSELoss(**kwargs),
        "mae": lambda: nn.L1Loss(**kwargs),
        "smooth_l1": lambda: nn.SmoothL1Loss(**kwargs),
        "huber": lambda: nn.SmoothL1Loss(**kwargs),
        # 多标签
        "bce_with_logits": lambda: nn.BCEWithLogitsLoss(**kwargs),
        # 其他
        "kl_div": lambda: nn.KLDivLoss(**kwargs),
        "ctc": lambda: nn.CTCLoss(**kwargs),
    }

    loss_factory = loss_map.get(loss_type)
    if loss_factory is None:
        raise ValueError(
            f"Unsupported loss type: {loss_type}. "
            f"Choose from {list(loss_map.keys())}"
        )
    return loss_factory()


# ========================================================================
# 优化器工厂
# ========================================================================
def create_optimizer(
    optimizer_type: OptimizerType,
    parameters: list[torch.nn.Parameter],
    **kwargs
) -> torch.optim.Optimizer:
    """
    创建优化器实例

    Args:
        optimizer_type: 优化器类型
        parameters: 模型参数列表
        **kwargs: 传递给优化器的额外参数（如 lr, weight_decay）

    Returns:
        PyTorch 优化器实例

    Examples:
        >>> optimizer = create_optimizer("adam", model.parameters(), lr=0.001)
        >>> optimizer = create_optimizer("sgd", model.parameters(), lr=0.01, momentum=0.9)
    """
    # 设置默认学习率
    kwargs.setdefault("lr", 0.001)

    optimizer_map: dict[OptimizerType, type[torch.optim.Optimizer]] = {
        "adam": torch.optim.Adam,
        "adamw": torch.optim.AdamW,
        "sgd": torch.optim.SGD,
        "rmsprop": torch.optim.RMSprop,
        "adagrad": torch.optim.Adagrad,
    }

    optimizer_cls = optimizer_map.get(optimizer_type)
    if optimizer_cls is None:
        raise ValueError(
            f"Unsupported optimizer: {optimizer_type}. "
            f"Choose from {list(optimizer_map.keys())}"
        )
    return optimizer_cls(parameters, **kwargs)
