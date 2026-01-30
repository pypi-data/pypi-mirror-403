"""
ML Magic - 极致简化的 ML API

设计理念:
- 从想法到结果，只需要一行代码
- 自动处理所有脏活累活：数据加载、预处理、模型选择、训练
- 智能默认值，但保留完全控制权
- 函数式 API，简洁优雅

核心原则:
    "Don't make me think about boilerplate"
    "Just give me the result"
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Optional, Any, Dict, List
from dataclasses import dataclass, field
import warnings

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, TensorDataset, DataLoader
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from .models import SimpleModel
from .trainers.auto import AutoTrainer, TrainerConfig, TrainingHistory


# ========================================================================
# 结果对象
# ========================================================================
@dataclass
class TrainResult:
    """训练结果 - 包含所有你需要的"""
    model: Any
    history: TrainingHistory
    metrics: Dict[str, float] = field(default_factory=dict)
    predictions: Optional[np.ndarray] = None

    def __repr__(self) -> str:
        acc = self.metrics.get('accuracy', self.metrics.get('val_accuracy', 0))
        return f"<TrainResult: model={self.model.__class__.__name__}, accuracy={acc:.4f}>"


# ========================================================================
# Level 1: 从原始数据到训练结果 - 一行代码
# ========================================================================
def train(
    data: Union[str, Path, pd.DataFrame, np.ndarray, tuple],
    target: Optional[Union[str, int, np.ndarray]] = None,
    task: str = "auto",
    test_size: float = 0.2,
    epochs: int = 100,
    hidden_layers: Optional[List[int]] = None,
    **kwargs
) -> TrainResult:
    """
    🪄 一行代码完成从数据到训练模型

    自动处理:
    - 数据加载（CSV/Excel/NumPy/Pandas）
    - 数据预处理（标准化、编码）
    - 数据集划分
    - 模型架构选择
    - 训练循环
    - 评估

    Args:
        data: 输入数据，支持多种格式:
            - str/Path: CSV/Excel 文件路径
            - pd.DataFrame: Pandas DataFrame
            - np.ndarray: NumPy 数组
            - tuple: (X, y) 元组
        target: 目标列:
            - str: 列名（用于 DataFrame）
            - int: 列索引（用于 NumPy）
            - np.ndarray: 独立的标签数组
            - None: data 是 (X, y) 元组时
        task: 任务类型:
            - "auto": 自动检测（默认）
            - "classification": 分类
            - "regression": 回归
            - "binary": 二分类
        test_size: 测试集比例
        epochs: 训练轮数
        hidden_layers: 隐藏层大小，如 [64, 32]
        **kwargs: 其他训练参数

    Returns:
        TrainResult 包含模型、历史、指标

    Examples:
        >>> # CSV 文件 - 分类任务
        >>> result = train("iris.csv", target="species", epochs=50)
        >>> print(f"Accuracy: {result.metrics['accuracy']:.2%}")

        >>> # NumPy 数组 - 回归任务
        >>> X = np.random.randn(1000, 20)
        >>> y = np.random.randn(1000)
        >>> result = train((X, y), task="regression")

        >>> # DataFrame - 二分类
        >>> df = pd.read_csv("data.csv")
        >>> result = train(df, target="label", task="binary", hidden_layers=[128, 64])
    """
    if not TORCH_AVAILABLE:
        raise ImportError(
            "PyTorch is required for training. "
            "Install it with: pip install torch"
        )

    # ========== 步骤 1: 数据加载 ==========
    X, y, feature_names = _load_data(data, target)

    # ========== 步骤 2: 自动检测任务类型 ==========
    if task == "auto":
        task = _detect_task_type(y, n_classes=len(np.unique(y)) if len(y.shape) == 1 else None)

    # ========== 步骤 3: 数据预处理 ==========
    X_processed, y_processed, preprocessors = _preprocess_data(X, y, task)

    # ========== 步骤 4: 数据集划分 ==========
    X_train, X_val, y_train, y_val = train_test_split(
        X_processed, y_processed,
        test_size=test_size,
        random_state=42,
        stratify=y_processed if task != "regression" else None
    )

    # ========== 步骤 5: 创建数据加载器 ==========
    train_loader, val_loader = _create_dataloaders(
        X_train, y_train, X_val, y_val,
        batch_size=kwargs.get('batch_size', 32)
    )

    # ========== 步骤 6: 自动设计模型架构 ==========
    input_size = X_train.shape[1]
    output_size = _get_output_size(y_train, task)

    if hidden_layers is None:
        hidden_layers = _suggest_hidden_layers(input_size, task)

    layers = [input_size] + hidden_layers + [output_size]
    model = SimpleModel(layers, task=task, **{k: v for k, v in kwargs.items()
                                               if k in ['activation', 'dropout', 'batch_norm']})

    # ========== 步骤 7: 训练 ==========
    config = TrainerConfig(
        epochs=epochs,
        task=task,
        **{k: v for k, v in kwargs.items() if k in TrainerConfig.__dataclass_fields__}
    )
    trainer = AutoTrainer(config)
    history = trainer.fit(model, train_loader, val_loader)

    # ========== 步骤 8: 评估 ==========
    metrics = _evaluate_model(model, val_loader, task)

    return TrainResult(
        model=model,
        history=history,
        metrics=metrics
    )


def predict(
    model: nn.Module,
    data: Union[str, Path, pd.DataFrame, np.ndarray],
    **kwargs
) -> np.ndarray:
    """
    🎯 一行代码进行预测

    Args:
        model: 训练好的模型
        data: 输入数据
        **kwargs: 额外参数

    Returns:
        预测结果数组

    Examples:
        >>> predictions = predict(model, "test.csv")
        >>> predictions = predict(model, X_new)
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch is required")

    # 加载数据
    if isinstance(data, (str, Path)):
        data = pd.read_csv(data)

    if isinstance(data, pd.DataFrame):
        X = data.values
    else:
        X = np.array(data)

    # 转换为 tensor
    X_tensor = torch.FloatTensor(X)

    # 预测
    model.eval()
    with torch.no_grad():
        predictions = model(X_tensor)

    # 根据任务类型处理输出
    if hasattr(model, 'task'):
        task = model.task
        if task == "classification":
            return predictions.argmax(dim=1).numpy()
        elif task == "binary":
            return (predictions > 0.5).float().numpy()
        else:
            return predictions.numpy()

    return predictions.numpy()


# ========================================================================
# Level 2: 常见任务专用的 one-liner
# ========================================================================
def tabular_classifier(
    data: Union[str, pd.DataFrame],
    target: str,
    *,
    epochs: int = 100,
    hidden_layers: Optional[List[int]] = None,
    **kwargs
) -> TrainResult:
    """
    📊 表格数据分类 - 一行代码

    专门为结构化表格数据（CSV、Excel）优化

    Examples:
        >>> result = tabular_classifier("customer_data.csv", "churn", epochs=50)
        >>> print(f"Churn prediction accuracy: {result.metrics['accuracy']:.2%}")
    """
    return train(
        data=data,
        target=target,
        task="classification",
        epochs=epochs,
        hidden_layers=hidden_layers,
        **kwargs
    )


def regressor(
    data: Union[str, pd.DataFrame, tuple],
    target: Optional[Union[str, np.ndarray]] = None,
    *,
    epochs: int = 100,
    hidden_layers: Optional[List[int]] = None,
    **kwargs
) -> TrainResult:
    """
    📈 回归任务 - 一行代码

    Examples:
        >>> result = regressor("house_prices.csv", "price")
        >>> result = regressor((X, y), epochs=200)
        >>> predictions = result.model.predict(X_test)
    """
    return train(
        data=data,
        target=target,
        task="regression",
        epochs=epochs,
        hidden_layers=hidden_layers,
        **kwargs
    )


def binary_classifier(
    data: Union[str, pd.DataFrame],
    target: str,
    *,
    epochs: int = 100,
    hidden_layers: Optional[List[int]] = None,
    **kwargs
) -> TrainResult:
    """
    🎯 二分类任务 - 一行代码

    Examples:
        >>> result = binary_classifier("fraud_data.csv", "is_fraud")
        >>> print(f"Fraud detection AUC: {result.metrics['auc']:.4f}")
    """
    return train(
        data=data,
        target=target,
        task="binary",
        epochs=epochs,
        hidden_layers=hidden_layers,
        **kwargs
    )


# ========================================================================
# 辅助函数
# ========================================================================
def _load_data(
    data: Union[str, Path, pd.DataFrame, np.ndarray, tuple],
    target: Optional[Union[str, int, np.ndarray]]
) -> tuple[np.ndarray, np.ndarray, Optional[List[str]]]:
    """加载并返回 X, y"""

    # 情况 1: (X, y) 元组
    if isinstance(data, tuple):
        X, y = data
        return np.array(X), np.array(y), None

    # 情况 2: 文件路径
    if isinstance(data, (str, Path)):
        path = Path(data)
        if path.suffix in ['.csv', '.csv.gz']:
            df = pd.read_csv(data)
        elif path.suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(data)
        elif path.suffix == '.parquet':
            df = pd.read_parquet(data)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        feature_names = df.columns.tolist()
        if isinstance(target, str):
            y = df[target].values
            X = df.drop(columns=[target]).values
            feature_names.remove(target)
        else:
            raise ValueError("target must be a column name for file inputs")

        return X, y, feature_names

    # 情况 3: DataFrame
    if isinstance(data, pd.DataFrame):
        feature_names = data.columns.tolist()
        if isinstance(target, str):
            y = data[target].values
            X = data.drop(columns=[target]).values
            feature_names.remove(target)
        elif isinstance(target, int):
            y = data.iloc[:, target].values
            X = data.drop(columns=data.columns[target]).values
            feature_names.pop(target)
        elif isinstance(target, np.ndarray):
            X = data.values
            y = target
        else:
            raise ValueError(f"Invalid target type: {type(target)}")

        return X, y, feature_names

    # 情况 4: NumPy array
    if isinstance(data, np.ndarray):
        if isinstance(target, np.ndarray):
            return data, target, None
        elif isinstance(target, int):
            X = np.delete(data, target, axis=1)
            y = data[:, target]
            return X, y, None
        else:
            raise ValueError("For numpy arrays, target must be an int or array")

    raise ValueError(f"Unsupported data type: {type(data)}")


def _detect_task_type(y: np.ndarray, n_classes: Optional[int] = None) -> str:
    """自动检测任务类型"""
    unique_values = np.unique(y)
    n_classes = len(unique_values) if n_classes is None else n_classes

    # 浮点数 = 回归
    if y.dtype in [np.float32, np.float64]:
        if n_classes <= 10:  # 少量浮点数可能是编码的类别
            return "classification"
        return "regression"

    # 整数 - 判断是分类还是回归
    if y.dtype in [np.int32, np.int64]:
        if n_classes == 2:
            return "binary"
        elif n_classes <= 100:  # 少量类别 = 分类
            return "classification"
        else:  # 大量整数 = 回归
            return "regression"

    # 默认分类
    return "classification"


def _preprocess_data(
    X: np.ndarray,
    y: np.ndarray,
    task: str
) -> tuple[np.ndarray, np.ndarray, dict]:
    """数据预处理"""
    preprocessors = {}

    # 特征标准化（回归任务需要）
    if task == "regression":
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        preprocessors['scaler'] = scaler

    # 标签编码（分类任务）
    if task in ["classification", "binary"]:
        if y.dtype == object or y.dtype.kind in ['U', 'O', 'S']:
            encoder = LabelEncoder()
            y = encoder.fit_transform(y)
            preprocessors['label_encoder'] = encoder

    return X, y, preprocessors


def _create_dataloaders(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    batch_size: int
) -> tuple[DataLoader, DataLoader]:
    """创建 PyTorch 数据加载器"""
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train),
        torch.LongTensor(y_train) if y_train.dtype.kind in ['i', 'u'] else torch.FloatTensor(y_train)
    )
    val_dataset = TensorDataset(
        torch.FloatTensor(X_val),
        torch.LongTensor(y_val) if y_val.dtype.kind in ['i', 'u'] else torch.FloatTensor(y_val)
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader


def _get_output_size(y: np.ndarray, task: str) -> int:
    """获取输出层大小"""
    if task == "regression":
        return 1
    elif task == "binary":
        return 1
    else:  # classification
        return len(np.unique(y))


def _suggest_hidden_layers(input_size: int, task: str) -> List[int]:
    """根据输入大小自动建议隐藏层"""
    if task == "regression":
        # 回归任务：较简单的网络
        if input_size < 50:
            return [64, 32]
        elif input_size < 500:
            return [128, 64]
        else:
            return [256, 128, 64]
    else:
        # 分类任务：可以更复杂
        if input_size < 50:
            return [64, 32]
        elif input_size < 500:
            return [128, 64]
        else:
            return [256, 128, 64]


def _evaluate_model(
    model: nn.Module,
    data_loader: DataLoader,
    task: str
) -> Dict[str, float]:
    """评估模型并返回指标"""
    model.eval()
    device = next(model.parameters()).device

    all_preds = []
    all_labels = []
    total_loss = 0.0

    with torch.no_grad():
        for X_batch, y_batch in data_loader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)

            outputs = model(X_batch)
            all_preds.append(outputs.cpu())
            all_labels.append(y_batch.cpu())

    # 合并所有批次
    all_preds = torch.cat(all_preds)
    all_labels = torch.cat(all_labels)

    # 计算准确率
    if task == "classification":
        pred_classes = all_preds.argmax(dim=1)
        accuracy = (pred_classes == all_labels).float().mean().item()
        return {"accuracy": accuracy, "val_accuracy": accuracy}
    elif task == "binary":
        pred_classes = (all_preds > 0.5).long()
        accuracy = (pred_classes.squeeze() == all_labels).float().mean().item()
        return {"accuracy": accuracy, "val_accuracy": accuracy}
    else:  # regression
        mse = torch.nn.functional.mse_loss(all_preds, all_labels.unsqueeze(1)).item()
        return {"mse": mse, "val_mse": mse}


# ========================================================================
# 导出 API
# ========================================================================
__all__ = [
    "train",
    "predict",
    "tabular_classifier",
    "regressor",
    "binary_classifier",
    "TrainResult",
]
