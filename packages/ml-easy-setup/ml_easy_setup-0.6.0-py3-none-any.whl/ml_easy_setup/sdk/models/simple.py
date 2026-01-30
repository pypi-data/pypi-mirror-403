"""
SimpleModel - 一行代码构建神经网络

设计理念:
- 隐藏 PyTorch nn.Module 的样板代码
- 支持通过层大小列表快速构建全连接网络
- 自动处理激活函数和输出层
- 保持与原生 PyTorch 的完全兼容性
"""

from __future__ import annotations

from typing import Sequence, Union, Optional
import torch
import torch.nn as nn

from ..utils.types import (
    ActivationType,
    TaskType,
    get_activation,
)


# ========================================================================
# SimpleModel - 核心模型构建器
# ========================================================================
class SimpleModel(nn.Module):
    """
    简单的顺序模型构建器 - 通过层大小列表快速构建神经网络

    设计原理:
    1. 使用声明式配置而非命令式代码
    2. 约定优于配置 - 根据任务类型自动选择输出层
    3. 完全兼容 PyTorch 生态 - 返回标准的 nn.Sequential

    参数说明:
        layers: 层大小列表，例如 [784, 128, 64, 10] 表示:
            - 输入层: 784 个特征
            - 隐藏层1: 128 个神经元
            - 隐藏层2: 64 个神经元
            - 输出层: 10 个类别

        activation: 隐藏层使用的激活函数，默认 'relu'
            可选: 'relu', 'gelu', 'selu', 'tanh', 'sigmoid', 'leaky_relu', 'silu', 'none'

        task: 任务类型，影响输出层设计:
            - 'classification': 多分类（默认）
            - 'binary': 二分类
            - 'regression': 回归
            - 'multilabel': 多标签分类

        dropout: Dropout 概率，0 表示不使用 dropout

        batch_norm: 是否在隐藏层使用批归一化

        output_activation: 输出层激活函数，None 表示根据 task 自动选择

    示例:
        >>> # 多分类 MLP
        >>> model = SimpleModel([784, 128, 10], task='classification')
        >>> >>> # 带正则化的回归模型
        >>> model = SimpleModel([20, 64, 32, 1], task='regression', dropout=0.2)
        >>> >>> # 二分类网络
        >>> model = SimpleModel([50, 100, 1], task='binary', activation='gelu')
    """

    def __init__(
        self,
        layers: Sequence[int],
        activation: ActivationType = "relu",
        task: TaskType = "classification",
        dropout: float = 0.0,
        batch_norm: bool = False,
        output_activation: Optional[ActivationType] = None,
    ):
        super().__init__()

        if len(layers) < 2:
            raise ValueError(
                f"layers must contain at least 2 elements (input and output sizes), "
                f"got {len(layers)}: {layers}"
            )

        self.input_size = layers[0]
        self.output_size = layers[-1]
        self.task = task
        self.activation_name = activation

        # 构建网络层
        self.model = self._build_network(
            layers=layers,
            activation=activation,
            task=task,
            dropout=dropout,
            batch_norm=batch_norm,
            output_activation=output_activation,
        )

    def _build_network(
        self,
        layers: Sequence[int],
        activation: ActivationType,
        task: TaskType,
        dropout: float,
        batch_norm: bool,
        output_activation: Optional[ActivationType],
    ) -> nn.Sequential:
        """
        构建网络结构

        构建策略:
        - 隐藏层: Linear -> (BatchNorm) -> (Dropout) -> Activation
        - 输出层: Linear -> (OutputActivation)
        """
        layers_list: list[nn.Module] = []

        # 构建隐藏层（不包括最后一层）
        for i in range(len(layers) - 2):
            in_features = layers[i]
            out_features = layers[i + 1]

            # 线性层
            layers_list.append(nn.Linear(in_features, out_features))

            # 批归一化（在激活函数之前）
            if batch_norm:
                layers_list.append(nn.BatchNorm1d(out_features))

            # Dropout
            if dropout > 0:
                layers_list.append(nn.Dropout(dropout))

            # 激活函数
            layers_list.append(get_activation(activation))

        # 输出层
        in_features = layers[-2]
        out_features = layers[-1]
        layers_list.append(nn.Linear(in_features, out_features))

        # 输出层激活函数
        if output_activation is not None:
            layers_list.append(get_activation(output_activation))
        else:
            # 根据任务类型自动选择输出激活
            layers_list.append(self._get_default_output_activation(task, out_features))

        return nn.Sequential(*layers_list)

    def _get_default_output_activation(
        self,
        task: TaskType,
        out_features: int,
    ) -> nn.Module:
        """
        根据任务类型获取默认的输出层激活函数

        设计决策:
        - classification: 不添加激活（在损失函数中处理 LogSoftmax）
        - binary: Sigmoid（将输出映射到 [0, 1]）
        - regression: Identity（线性输出）
        - multilabel: Sigmoid（每个标签独立概率）
        """
        if task == "classification":
            # PyTorch 的 CrossEntropyLoss 已经包含了 LogSoftmax
            return nn.Identity()
        elif task == "binary":
            return nn.Sigmoid()
        elif task == "regression":
            return nn.Identity()
        elif task == "multilabel":
            return nn.Sigmoid()
        else:
            return nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 输入张量，形状为 (batch_size, input_size)

        Returns:
            输出张量，形状为 (batch_size, output_size)
        """
        return self.model(x)

    def summary(self) -> str:
        """
        打印模型摘要信息

        Returns:
            模型摘要字符串
        """
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)

        lines = [
            "=" * 50,
            "SimpleModel Summary",
            "=" * 50,
            f"Input Size:      {self.input_size}",
            f"Output Size:     {self.output_size}",
            f"Task:            {self.task}",
            f"Activation:      {self.activation_name}",
            "-" * 50,
            f"Total Params:    {total_params:,}",
            f"Trainable Params: {trainable_params:,}",
            "=" * 50,
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"SimpleModel(layers={list(self.model)}, "
            f"task='{self.task}', "
            f"activation='{self.activation_name}')"
        )


# ========================================================================
# SequentialBuilder - 别名，提供更灵活的 API
# ========================================================================
SequentialBuilder = SimpleModel


# ========================================================================
# 辅助函数
# ========================================================================
def mlp(
    input_size: int,
    hidden_sizes: list[int],
    output_size: int,
    **kwargs
) -> SimpleModel:
    """
    快速创建多层感知机的便捷函数

    Args:
        input_size: 输入特征维度
        hidden_sizes: 隐藏层大小列表
        output_size: 输出维度
        **kwargs: 传递给 SimpleModel 的其他参数

    Returns:
        SimpleModel 实例

    Examples:
        >>> model = mlp(784, [128, 64], 10, task='classification')
        >>> model = mlp(20, [64, 32], 1, task='regression')
    """
    layers = [input_size] + hidden_sizes + [output_size]
    return SimpleModel(layers, **kwargs)


# ========================================================================
# 预定义模型架构
# ========================================================================
class MLPFactory:
    """
    常用 MLP 架构的工厂类

    提供:
    - 经典的 MLP 结构
    - 针对不同任务优化的默认配置
    - 一行代码即可使用
    """

    @staticmethod
    def mnist(hidden_sizes: list[int] | None = None) -> SimpleModel:
        """
        MNIST 分类模型 (28x28 = 784 输入, 10 类别)

        默认结构: [784, 128, 64, 10]
        """
        if hidden_sizes is None:
            hidden_sizes = [128, 64]
        return SimpleModel([784] + hidden_sizes + [10], task="classification")

    @staticmethod
    def cifar(hidden_sizes: list[int] | None = None) -> SimpleModel:
        """
        CIFAR-10 分类模型 (32x32x3 = 3072 输入, 10 类别)

        默认结构: [3072, 256, 128, 10]
        """
        if hidden_sizes is None:
            hidden_sizes = [256, 128]
        return SimpleModel([3072] + hidden_sizes + [10], task="classification")

    @staticmethod
    def binary_classifier(
        input_size: int,
        hidden_sizes: list[int] | None = None,
    ) -> SimpleModel:
        """
        二分类模型

        Args:
            input_size: 输入特征维度
            hidden_sizes: 隐藏层大小，默认 [64, 32]

        Returns:
            二分类 SimpleModel
        """
        if hidden_sizes is None:
            hidden_sizes = [64, 32]
        return SimpleModel([input_size] + hidden_sizes + [1], task="binary")

    @staticmethod
    def regressor(
        input_size: int,
        hidden_sizes: list[int] | None = None,
    ) -> SimpleModel:
        """
        回归模型

        Args:
            input_size: 输入特征维度
            hidden_sizes: 隐藏层大小，默认 [64, 32]

        Returns:
            回归 SimpleModel
        """
        if hidden_sizes is None:
            hidden_sizes = [64, 32]
        return SimpleModel([input_size] + hidden_sizes + [1], task="regression")
