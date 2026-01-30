"""
AutoTrainer - 自动训练循环抽象

设计理念:
- 一行代码完成模型训练: trainer.fit(model, data, epochs=100)
- 自动处理设备选择、损失函数、优化器
- 内置进度条和日志输出
- 保持与原生 PyTorch 的完全兼容性
"""

from __future__ import annotations

from typing import Optional, Union, Callable
from dataclasses import dataclass, field
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import Optimizer

try:
    from tqdm.auto import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from ..utils.types import (
    TaskType,
    LossType,
    OptimizerType,
    DeviceType,
    get_default_loss,
    create_loss,
    create_optimizer,
)
from ..utils.device import get_device, detect_device


# ========================================================================
# 训练配置
# ========================================================================
@dataclass
class TrainerConfig:
    """
    训练器配置类

    设计原理:
    - 使用 dataclass 提供默认值和类型检查
    - 集中管理所有超参数
    - 便于配置序列化和复现
    """

    # 训练参数
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    weight_decay: float = 0.0

    # 优化器配置
    optimizer: OptimizerType = "adam"

    # 损失函数配置
    loss: Optional[LossType] = None  # None 表示根据 task 自动选择
    task: TaskType = "classification"

    # 设备配置
    device: DeviceType = "auto"

    # 训练行为
    gradient_clip_val: Optional[float] = None  # 梯度裁剪阈值
    accumulate_grad_batches: int = 1  # 梯度累积步数

    # 验证
    val_freq: int = 1  # 验证频率（每 N 个 epoch）
    early_stopping_patience: Optional[int] = None  # 早停耐心值

    # 日志
    verbose: bool = True
    log_freq: int = 10  # 每 N 个 batch 打印一次


# ========================================================================
# 训练历史
# ========================================================================
@dataclass
class TrainingHistory:
    """训练历史记录"""

    train_loss: list[float] = field(default_factory=list)
    val_loss: list[float] = field(default_factory=list)
    train_metrics: dict[str, list[float]] = field(default_factory=dict)
    val_metrics: dict[str, list[float]] = field(default_factory=dict)
    epoch_times: list[float] = field(default_factory=list)

    def add_epoch(
        self,
        train_loss: float,
        val_loss: Optional[float] = None,
        train_metrics: dict[str, float] | None = None,
        val_metrics: dict[str, float] | None = None,
        epoch_time: float = 0.0,
    ) -> None:
        self.train_loss.append(train_loss)
        if val_loss is not None:
            self.val_loss.append(val_loss)
        if train_metrics:
            for key, value in train_metrics.items():
                if key not in self.train_metrics:
                    self.train_metrics[key] = []
                self.train_metrics[key].append(value)
        if val_metrics:
            for key, value in val_metrics.items():
                if key not in self.val_metrics:
                    self.val_metrics[key] = []
                self.val_metrics[key].append(value)
        self.epoch_times.append(epoch_time)

    @property
    def best_epoch(self) -> int:
        """返回验证损失最低的 epoch 索引"""
        if not self.val_loss:
            return 0
        return int(torch.tensor(self.val_loss).argmin().item())

    @property
    def best_val_loss(self) -> float:
        """返回最佳验证损失"""
        if not self.val_loss:
            return min(self.train_loss) if self.train_loss else float("inf")
        return min(self.val_loss)


# ========================================================================
# AutoTrainer - 核心训练器
# ========================================================================
class AutoTrainer:
    """
    自动训练器 - 抽象完整的训练循环

    设计理念:
    1. 约定优于配置 - 根据 task 自动选择损失函数
    2. 单一职责 - 专注于训练逻辑，数据处理交由 DataLoader
    3. 可扩展 - 支持自定义指标、回调函数
    4. 零依赖 - 仅依赖 PyTorch，tqdm 为可选

    参数说明:
        config: 训练配置对象，如果为 None 则使用默认配置

    示例:
        >>> # 最简单的用法 - 使用所有默认配置
        >>> trainer = AutoTrainer()
        >>> trainer.fit(model, train_loader, epochs=50)
        >>>
        >>> # 自定义配置
        >>> config = TrainerConfig(
        ...     epochs=100,
        ...     learning_rate=0.01,
        ...     optimizer="sgd"
        ... )
        >>> trainer = AutoTrainer(config)
        >>> trainer.fit(model, train_loader, val_loader=val_loader)
    """

    def __init__(self, config: Optional[TrainerConfig] = None):
        self.config = config or TrainerConfig()
        self.device: torch.device = get_device(self.config.device)
        self.history = TrainingHistory()
        self._model: Optional[nn.Module] = None
        self._optimizer: Optional[Optimizer] = None
        self._loss_fn: Optional[nn.Module] = None

    # ====================================================================
    # 核心训练方法
    # ====================================================================
    def fit(
        self,
        model: nn.Module,
        train_data: Union[DataLoader, Dataset],
        val_data: Optional[Union[DataLoader, Dataset]] = None,
        epochs: Optional[int] = None,
        loss_fn: Optional[nn.Module] = None,
        optimizer: Optional[Optimizer] = None,
    ) -> TrainingHistory:
        """
        训练模型

        Args:
            model: PyTorch 模型
            train_data: 训练数据 (DataLoader 或 Dataset)
            val_data: 验证数据 (可选)
            epochs: 训练轮数，覆盖配置中的值
            loss_fn: 自定义损失函数（可选）
            optimizer: 自定义优化器（可选）

        Returns:
            TrainingHistory 训练历史对象

        Examples:
            >>> trainer = AutoTrainer()
            >>> history = trainer.fit(model, train_loader, epochs=50)
            >>> print(f"Best val loss: {history.best_val_loss:.4f}")
        """
        # 设置 epoch 数量
        if epochs is not None:
            self.config.epochs = epochs

        # 设置模型
        self._model = model.to(self.device)

        # 设置损失函数
        if loss_fn is not None:
            self._loss_fn = loss_fn
        else:
            loss_type = self.config.loss or get_default_loss(self.config.task)
            self._loss_fn = create_loss(loss_type)

        # 设置优化器
        if optimizer is not None:
            self._optimizer = optimizer
        else:
            self._optimizer = create_optimizer(
                self.config.optimizer,
                model.parameters(),
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay,
            )

        # 处理数据
        train_loader = self._to_dataloader(train_data, shuffle=True)
        val_loader = self._to_dataloader(val_data, shuffle=False) if val_data else None

        # 打印训练信息
        if self.config.verbose:
            self._print_training_info(len(train_loader), val_loader is not None)

        # 训练循环
        patience_counter = 0
        best_val_loss = float("inf")

        for epoch in range(self.config.epochs):
            epoch_start = time.time()

            # 训练一个 epoch
            train_loss = self._train_epoch(train_loader)

            # 验证
            val_loss = None
            if val_loader is not None and (epoch + 1) % self.config.val_freq == 0:
                val_loss = self._validate(val_loader)

            # 记录历史
            epoch_time = time.time() - epoch_start
            self.history.add_epoch(train_loss, val_loss, epoch_time=epoch_time)

            # 打印进度
            if self.config.verbose:
                self._print_epoch_progress(epoch, train_loss, val_loss)

            # 早停检查
            if val_loss is not None:
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= self.config.early_stopping_patience:
                        if self.config.verbose:
                            print(f"\nEarly stopping at epoch {epoch + 1}")
                        break

        return self.history

    def _train_epoch(self, train_loader: DataLoader) -> float:
        """训练一个 epoch"""
        self._model.train()
        total_loss = 0.0
        num_batches = len(train_loader)

        # 创建进度条
        iterator = range(num_batches)
        if TQDM_AVAILABLE and self.config.verbose:
            iterator = tqdm(iterator, desc="Training", leave=False)

        for batch_idx in iterator:
            batch = self._get_batch(train_loader, batch_idx)

            # 前向传播
            loss = self._compute_loss(batch)

            # 反向传播
            if self.config.accumulate_grad_batches > 1:
                loss = loss / self.config.accumulate_grad_batches

            loss.backward()

            # 梯度累积
            if (batch_idx + 1) % self.config.accumulate_grad_batches == 0:
                # 梯度裁剪
                if self.config.gradient_clip_val is not None:
                    torch.nn.utils.clip_grad_norm_(
                        self._model.parameters(),
                        self.config.gradient_clip_val
                    )

                self._optimizer.step()
                self._optimizer.zero_grad()

            total_loss += loss.item()

        return total_loss / num_batches

    def _validate(self, val_loader: DataLoader) -> float:
        """验证模型"""
        self._model.eval()
        total_loss = 0.0
        num_batches = len(val_loader)

        with torch.no_grad():
            for batch_idx in range(num_batches):
                batch = self._get_batch(val_loader, batch_idx)
                loss = self._compute_loss(batch)
                total_loss += loss.item()

        return total_loss / num_batches

    def _compute_loss(self, batch: tuple[torch.Tensor, ...]) -> torch.Tensor:
        """计算损失"""
        if len(batch) == 2:
            # 标准 (x, y) 格式
            x, y = batch
            x = x.to(self.device)
            y = y.to(self.device)

            # 特殊处理回归和二分类的形状
            if self.config.task in ["regression", "binary"]:
                y = y.unsqueeze(1).float() if y.dim() == 1 else y.float()

            predictions = self._model(x)
            return self._loss_fn(predictions, y)

        # 自定义 batch 格式
        raise ValueError(
            f"Unsupported batch format: expected (x, y), got shape {len(batch)}"
        )

    # ====================================================================
    # 辅助方法
    # ====================================================================
    def _to_dataloader(
        self,
        data: Union[DataLoader, Dataset, None],
        shuffle: bool = False
    ) -> Optional[DataLoader]:
        """将数据转换为 DataLoader"""
        if data is None:
            return None
        if isinstance(data, DataLoader):
            return data
        return DataLoader(
            data,
            batch_size=self.config.batch_size,
            shuffle=shuffle,
        )

    def _get_batch(self, loader: DataLoader, idx: int) -> tuple[torch.Tensor, ...]:
        """获取指定索引的 batch"""
        # 简化实现：直接遍历获取
        # 生产环境可以优化为使用迭代器
        for i, batch in enumerate(loader):
            if i == idx:
                return batch
        raise IndexError(f"Batch index {idx} out of range")

    def _print_training_info(self, num_train_batches: int, has_val: bool) -> None:
        """打印训练开始信息"""
        print("\n" + "=" * 50)
        print("AutoTrainer - Starting Training")
        print("=" * 50)
        print(f"Device:        {self.device}")
        print(f"Epochs:        {self.config.epochs}")
        print(f"Batch size:    {self.config.batch_size}")
        print(f"Optimizer:     {self.config.optimizer}")
        print(f"Learning rate: {self.config.learning_rate}")
        print(f"Train batches: {num_train_batches}")
        if has_val:
            print(f"Validation:    Enabled")
        print("=" * 50 + "\n")

    def _print_epoch_progress(
        self,
        epoch: int,
        train_loss: float,
        val_loss: Optional[float]
    ) -> None:
        """打印 epoch 进度"""
        if (epoch + 1) % self.config.log_freq != 0:
            return

        msg = f"Epoch [{epoch + 1}/{self.config.epochs}] - Train Loss: {train_loss:.4f}"
        if val_loss is not None:
            msg += f" | Val Loss: {val_loss:.4f}"
        print(msg)

    # ====================================================================
    # 预测方法
    # ====================================================================
    def predict(self, x: torch.Tensor) -> torch.Tensor:
        """
        进行预测

        Args:
            x: 输入张量

        Returns:
            预测结果
        """
        if self._model is None:
            raise RuntimeError("Model not trained. Call fit() first.")

        self._model.eval()
        with torch.no_grad():
            x = x.to(self.device)
            predictions = self._model(x)

            # 根据任务类型处理输出
            if self.config.task == "classification":
                return predictions.argmax(dim=1)
            elif self.config.task == "binary":
                return (predictions > 0.5).float()
            else:
                return predictions

    def evaluate(
        self,
        model: nn.Module,
        test_data: Union[DataLoader, Dataset],
        metric_fn: Optional[Callable] = None,
    ) -> dict[str, float]:
        """
        评估模型

        Args:
            model: 要评估的模型
            test_data: 测试数据
            metric_fn: 自定义指标函数

        Returns:
            包含评估指标的字典
        """
        model.eval()
        model = model.to(self.device)

        test_loader = self._to_dataloader(test_data, shuffle=False)
        total_loss = 0.0
        num_batches = len(test_loader)

        with torch.no_grad():
            for batch_idx in range(num_batches):
                batch = self._get_batch(test_loader, batch_idx)
                loss = self._compute_loss(batch)
                total_loss += loss.item()

        results = {"loss": total_loss / num_batches}

        if metric_fn is not None:
            # 执行自定义指标计算
            results.update(metric_fn(model, test_loader))

        return results


# ========================================================================
# 便捷函数
# ========================================================================
def fit(
    model: nn.Module,
    train_data: Union[DataLoader, Dataset],
    epochs: int = 100,
    **kwargs
) -> TrainingHistory:
    """
    一行代码训练模型的便捷函数

    Args:
        model: PyTorch 模型
        train_data: 训练数据
        epochs: 训练轮数
        **kwargs: 传递给 AutoTrainer 的其他参数

    Returns:
        TrainingHistory 训练历史

    Examples:
        >>> history = fit(model, train_loader, epochs=50)
    """
    config = TrainerConfig(epochs=epochs, **kwargs)
    trainer = AutoTrainer(config)
    return trainer.fit(model, train_data)


# ========================================================================
# 通用指标函数
# ========================================================================
def accuracy_score(
    model: nn.Module,
    data_loader: DataLoader,
    device: Optional[torch.device] = None,
) -> float:
    """
    计算分类准确率

    Args:
        model: 模型
        data_loader: 数据加载器
        device: 设备

    Returns:
        准确率 (0-1)
    """
    if device is None:
        device = detect_device()

    model.eval()
    model = model.to(device)

    correct = 0
    total = 0

    with torch.no_grad():
        for x, y in data_loader:
            x = x.to(device)
            y = y.to(device)

            predictions = model(x)
            _, predicted = torch.max(predictions.data, 1)
            total += y.size(0)
            correct += (predicted == y).sum().item()

    return correct / total if total > 0 else 0.0
