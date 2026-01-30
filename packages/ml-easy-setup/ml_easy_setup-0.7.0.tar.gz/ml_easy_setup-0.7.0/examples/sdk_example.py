"""
mles SDK 快速入门示例

运行此脚本来验证 SDK 是否正常工作
"""

# =============================================================================
# 示例 1: 最简单的用法
# =============================================================================
print("=" * 60)
print("示例 1: 最简单的用法 - 创建模型并训练")
print("=" * 60)

import torch
from torch.utils.data import TensorDataset

# 导入 mles SDK
from ml_easy_setup import SimpleModel, AutoTrainer

# 1. 创建模拟数据
X = torch.randn(1000, 20)  # 1000 个样本，20 个特征
y = torch.randint(0, 3, (1000,))  # 3 类分类
train_dataset = TensorDataset(X, y)

# 2. 创建模型 (一行代码!)
model = SimpleModel([20, 64, 32, 3], task='classification')
print("\n模型创建成功!")
print(model.summary())

# 3. 训练模型 (一行代码!)
trainer = AutoTrainer()
history = trainer.fit(model, train_dataset, epochs=5)

print(f"\n训练完成! 最终损失: {history.train_loss[-1]:.4f}")


# =============================================================================
# 示例 2: 设备检测
# =============================================================================
print("\n" + "=" * 60)
print("示例 2: 自动设备检测")
print("=" * 60)

from ml_easy_setup import get_device, print_device_info

print("\n当前设备:")
device = get_device()
print(f"  {device}")

print("\n设备详细信息:")
print_device_info()


# =============================================================================
# 示例 3: 回归任务
# =============================================================================
print("\n" + "=" * 60)
print("示例 3: 回归任务")
print("=" * 60)

# 创建回归数据
X_reg = torch.randn(500, 10)
y_reg = torch.randn(500)
reg_dataset = TensorDataset(X_reg, y_reg)

# 创建回归模型
reg_model = SimpleModel([10, 32, 16, 1], task='regression', dropout=0.2)

# 训练
reg_trainer = AutoTrainer()
reg_history = reg_trainer.fit(reg_model, reg_dataset, epochs=5)

print(f"\n回归训练完成! 最终损失: {reg_history.train_loss[-1]:.4f}")


# =============================================================================
# 示例 4: 使用预定义模型
# =============================================================================
print("\n" + "=" * 60)
print("示例 4: 使用预定义模型架构")
print("=" * 60)

from ml_easy_setup import MLPFactory

# MNIST 模型
mnist_model = MLPFactory.mnist()
print(f"\nMNIST 模型: {mnist_model}")

# 二分类模型
binary_model = MLPFactory.binary_classifier(input_size=50)
print(f"二分类模型: {binary_model}")

# 回归模型
regressor = MLPFactory.regressor(input_size=15)
print(f"回归模型: {regressor}")


# =============================================================================
# 示例 5: 使用便捷函数
# =============================================================================
print("\n" + "=" * 60)
print("示例 5: 使用便捷函数 fit()")
print("=" * 60)

from ml_easy_setup import fit, mlp

# 一行创建模型
quick_model = mlp(20, [32, 16], 5, task='classification')

# 一行训练
quick_history = fit(quick_model, train_dataset, epochs=3)

print(f"\n快速训练完成! 最终损失: {quick_history.train_loss[-1]:.4f}")


print("\n" + "=" * 60)
print("所有示例运行完成! mles SDK 工作正常!")
print("=" * 60)
