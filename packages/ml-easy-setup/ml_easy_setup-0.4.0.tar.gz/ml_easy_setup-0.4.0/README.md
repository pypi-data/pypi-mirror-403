# ML Easy Setup

> 一键配置机器学习/深度学习环境，让科研工作更专注于算法本身

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/pypi/v/ml-easy-setup.svg)](https://pypi.org/project/ml-easy-setup/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 为什么选择 ML Easy Setup？

**痛点**：配置 ML/DL 环境总是遇到各种问题
- ❌ PyTorch、TensorFlow 版本冲突
- ❌ CUDA 驱动与工具包不匹配
- ❌ 依赖关系复杂，小白不知道从何入手
- ❌ 每次换电脑都要重新配置半天
- ❌ 不知道模型构建需要哪些工具包

**解决方案**：一条命令搞定一切
- ✅ 自动检测硬件和 CUDA 版本
- ✅ 13 种预配置环境模板，覆盖各种 ML 场景
- ✅ 基于 uv 的高速包安装
- ✅ 完善的依赖冲突检测

## 📦 安装

```bash
pip install ml-easy-setup
```

如果使用国内镜像（如清华源），可能需要稍等同步时间，或直接使用官方源：

```bash
pip install ml-easy-setup -i https://pypi.org/simple
```

或使用 uv（更快）：

```bash
uv pip install ml-easy-setup
```

## 📋 环境模板详解

### 🎓 基础模板

#### `minimal` - 最小化配置
**适合场景**：入门学习、简单实验、快速验证想法

```bash
mlsetup create quick-test --template minimal
```

**包含工具**：
- NumPy, Pandas - 数据处理
- scikit-learn - 传统机器学习
- Matplotlib - 可视化
- Jupyter - 交互式开发

---

### 🧠 深度学习框架

#### `pytorch` - PyTorch 深度学习
**适合场景**：深度学习研究、神经网络开发、学术项目

```bash
mlsetup create my-dl-project --template pytorch --cuda auto
```

**包含工具**：
- PyTorch, torchvision, torchaudio - 完整深度学习框架
- TensorBoard - 训练监控
- Pillow - 图像处理

**示例代码**：
```python
import torch
import torch.nn as nn

# 创建简单神经网络
model = nn.Sequential(
    nn.Linear(784, 128),
    nn.ReLU(),
    nn.Linear(128, 10)
)

# 检查 GPU 可用性
if torch.cuda.is_available():
    model = model.cuda()
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")
```

---

#### `tensorflow` - TensorFlow 深度学习
**适合场景**：TensorFlow 生态项目、TF Serving 部署

```bash
mlsetup create tf-project --template tensorflow --cuda auto
```

**包含工具**：
- TensorFlow, Keras - 深度学习框架
- TensorBoard - 可视化

---

### 🌍 专项领域

#### `nlp` - 自然语言处理
**适合场景**：文本分类、机器翻译、问答系统、大模型微调

```bash
mlsetup create nlp-project --template nlp --cuda auto
```

**包含工具**：
- Transformers - Hugging Face 预训练模型
- Datasets - 海量 NLP 数据集
- Accelerate - 分布式训练加速

**示例代码**：
```python
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# 情感分析
classifier = pipeline("sentiment-analysis")
result = classifier("ML Easy Setup 真的很棒！")
print(result)  # [{'label': 'POSITIVE', 'score': 0.9998}]

# 加载预训练模型
tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
model = AutoModelForSequenceClassification.from_pretrained("bert-base-chinese")
```

---

#### `cv` - 计算机视觉
**适合场景**：图像分类、目标检测、图像分割

```bash
mlsetup create cv-project --template cv --cuda auto
```

**包含工具**：
- Torchvision - 视觉模型和数据集
- OpenCV - 图像处理
- Albumentations - 数据增强

**示例代码**：
```python
import torch
from torchvision import models, transforms
from PIL import Image

# 加载预训练 ResNet
model = models.resnet50(pretrained=True)
model.eval()

# 图像预处理
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
])

# 图像分类
img = Image.open("image.jpg")
img_t = transform(img)
batch_t = torch.unsqueeze(img_t, 0)

with torch.no_grad():
    output = model(batch_t)
```

---

#### `rl` - 强化学习
**适合场景**：智能体训练、游戏 AI、机器人控制

```bash
mlsetup create rl-project --template rl --cuda auto
```

**包含工具**：
- Gymnasium - 强化学习环境
- Stable-Baselines3 - 成熟算法实现

**示例代码**：
```python
from stable_baselines3 import PPO
from gymnasium import make

# 创建环境
env = make("CartPole-v1")

# 训练 PPO 智能体
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)

# 保存模型
model.save("ppo_cartpole")
```

---

### 🔧 模型构建与验证

#### `model-builder` - 模型构建环境 ⭐
**适合场景**：模型训练、超参数优化、实验跟踪、Kaggle 竞赛

```bash
mlsetup create model-project --template model-builder --cuda cpu
```

**包含工具**：
- **XGBoost / LightGBM / CatBoost** - 梯度提升三巨头
- **Optuna** - 自动超参数优化
- **MLflow** - 实验跟踪和模型管理
- **W&B** - 云端实验监控

**示例代码**：
```python
import optuna
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import cross_val_score

# 定义目标函数
def objective(trial):
    n_estimators = trial.suggest_int('n_estimators', 10, 100)
    max_depth = trial.suggest_int('max_depth', 2, 32)

    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth
    )

    data = load_breast_cancer()
    scores = cross_val_score(clf, data.data, data.target, cv=5)
    return scores.mean()

# 运行优化
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=50)

print(f'最佳参数: {study.best_params}')
print(f'最佳分数: {study.best_value:.4f}')
```

**MLflow 实验跟踪**：
```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import GradientBoostingClassifier

# 开始实验
with mlflow.start_run():
    model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5
    )
    model.fit(X_train, y_train)

    # 记录参数和指标
    mlflow.log_params(model.get_params())
    mlflow.log_metric("accuracy", model.score(X_test, y_test))

    # 保存模型
    mlflow.sklearn.log_model(model, "model")
```

---

#### `algorithm-validator` - 算法验证环境
**适合场景**：算法性能测试、基准对比、论文实验复现

```bash
mlsetup create algo-test --template algorithm-validator --cuda cpu
```

**包含工具**：
- **pytest** - 测试框架
- **pytest-benchmark** - 性能基准测试
- **Datasets** - 标准数据集
- **Evaluate** - 模型评估指标

**示例代码**：
```python
import pytest
import pytest_benchmark
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification

def test_model_performance(benchmark):
    # 准备数据
    X, y = make_classification(n_samples=1000, n_features=20)

    # 基准测试
    model = LogisticRegression()
    result = benchmark(model.fit, X, y)

    # 断言
    assert result.score(X, y) > 0.8

# 运行测试
# pytest test_model.py --benchmark-only
```

---

### 📊 数据科学

#### `data-science` - 数据科学环境
**适合场景**：数据分析、可视化、统计建模、商业智能

```bash
mlsetup create data-project --template data-science --cuda cpu
```

**包含工具**：
- **Polars** - 高性能 DataFrame（比 Pandas 快）
- **Dask** - 并行计算（处理大数据）
- **PyArrow** - 高效数据格式
- **Statsmodels** - 统计分析
- **Plotly / Seaborn / Altair** - 交互式可视化

**示例代码**：
```python
import polars as pl
import plotly.express as px

# 读取大数据（支持 CSV、Parquet 等）
df = pl.read_csv("large_dataset.csv")

# 高性能数据处理
result = (
    df
    .filter(pl.col("sales") > 1000)
    .group_by("category")
    .agg([
        pl.col("sales").sum().alias("total_sales"),
        pl.col("sales").mean().alias("avg_sales")
    ])
    .sort("total_sales", descending=True)
)

# 交互式可视化
fig = px.bar(result.to_pandas(), x="category", y="total_sales")
fig.show()
```

---

#### `gradient-boosting` - 梯度提升专用 ⭐
**适合场景**：Kaggle 竞赛、表格数据建模、特征工程

```bash
mlsetup create kaggle-project --template gradient-boosting --cuda cpu
```

**包含工具**：
- **XGBoost** - 极速梯度提升
- **LightGBM** - 内存高效
- **CatBoost** - 自动处理类别特征
- **SHAP** - 模型可解释性

**示例代码**：
```python
import xgboost as xgb
import shap
from sklearn.datasets import load_boston

# 加载数据
data = load_boston()
X, y = data.data, data.target

# 训练 XGBoost
model = xgb.XGBRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=6
)
model.fit(X, y)

# SHAP 可解释性分析
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)
shap.summary_plot(shap_values, X, feature_names=data.feature_names)
```

---

### 🚀 MLOps

#### `mlops` - MLOps 部署环境
**适合场景**：模型部署、API 服务、模型监控

```bash
mlsetup create api-service --template mlops --cuda cpu
```

**包含工具**：
- **BentoML** - 模型服务框架
- **FastAPI** - 高性能 API
- **MLflow** - 模型版本管理
- **DVC** - 数据版本控制

**示例代码**：
```python
from bentoml import Service, api
import numpy as np

service = Service("ml_model")

# 加载模型
model = mlflow.pyfunc.load_model("models:/my_model/Production")

@service.api(input=JSON(), output=JSON())
def predict(input_data):
    X = np.array(input_data["features"])
    prediction = model.predict(X)
    return {"prediction": prediction.tolist()}

# 运行服务
# bentoml serve service:svc
```

---

### ⏱ 时间序列

#### `timeseries` - 时间序列分析
**适合场景**：销量预测、股票分析、传感器数据

```bash
mlsetup create forecast-project --template timeseries --cuda cpu
```

**包含工具**：
- **Prophet** - Facebook 时间序列预测
- **statsmodels** - 统计时间序列
- **darts** - 统一时间序列接口

**示例代码**：
```python
from prophet import Prophet
import pandas as pd

# 准备数据
df = pd.DataFrame({
    'ds': pd.date_range('2023-01-01', periods=365),
    'y': np.random.randn(365).cumsum()
})

# 创建预测模型
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False
)
model.fit(df)

# 预测未来 30 天
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

# 可视化
fig = model.plot(forecast)
```

---

### 🕸 图学习

#### `graph` - 图神经网络
**适合场景**：社交网络分析、分子性质预测、推荐系统

```bash
mlsetup create graph-project --template graph --cuda auto
```

**包含工具**：
- **PyTorch Geometric** - 图神经网络库
- **DGL** - 深度图学习
- **NetworkX** - 图算法

**示例代码**：
```python
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
import torch

# 构建图数据
edge_index = torch.tensor([[0, 1, 1, 2],
                           [1, 0, 2, 1]], dtype=torch.long)
x = torch.tensor([[-1], [0], [1]], dtype=torch.float)

data = Data(x=x, edge_index=edge_index)

# 定义 GCN
class GCN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = GCNConv(1, 16)
        self.conv2 = GCNConv(16, 2)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index)
        return x

# 训练
model = GCN()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
```

---

### 🎯 完整环境

#### `full` - 完整工具链
**适合场景**：需要全方位工具的复杂项目

```bash
mlsetup create full-stack --template full --cuda auto
```

**包含所有领域的工具**，适合：
- 需要同时使用多种技术的项目
- 不确定需要哪些工具的探索阶段
- 教学演示环境

---

## 🔧 系统检测

检查您的系统环境：

```bash
mlsetup detect
```

输出示例：
```
系统环境检测
━━━━━━━━━━━━━━━━━━━━━━━━━━━
项目          检测结果
━━━━━━━━━━━━━━━━━━━━━━━━━━━
操作系统      Darwin
Python 版本   3.11.5
架构          arm64
CUDA          未安装
GPU           Apple Silicon (MPS)
UV            0.1.20
━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🏥 环境健康检查

新功能！检查项目环境状态，发现潜在问题：

```bash
mlsetup health
```

输出示例：
```
╭─ ML Easy Setup ─╮
│ 环境健康检查    │
│ 状态: ⚠ WARNING │
╰─────────────────╯

健康分数:
  ✓ venv: ████████████████████ 100%
  ⚠ dependencies: ██████████████░░░░░░ 70%
  ✓ gpu: ████████████████████ 100%
  ✓ compatibility: ████████████████████ 100%
  ✓ disk: ████████████████████ 100%

发现的问题:
  ⚠ 发现依赖冲突或不兼容
  ⚠ nvidia-smi 不可用（无 NVIDIA GPU）

建议:
  1. ✓ 使用 uv 包管理器
  2. 运行: uv pip check 查看详细冲突信息
  3. 💡 PyTorch 版本问题 - 访问 https://pytorch.org 获取正确安装命令
```

自动修复问题：
```bash
mlsetup health --auto-fix
```

**检查项目**：
- 虚拟环境状态（支持 uv）
- 依赖冲突（通过 `uv pip check` 或 `pip check`）
- GPU/CUDA 可用性
- 包版本兼容性
- 磁盘空间

## 📦 添加额外的包

```bash
# 添加到核心依赖
mlsetup add numpy pandas

# 添加到开发依赖
mlsetup add pytest --dev
```

## 🏗️ 项目结构

创建的项目包含以下结构：

```
my-project/
├── .venv/              # 虚拟环境
├── src/                # 源代码目录
├── tests/              # 测试目录
├── data/               # 数据目录
├── notebooks/          # Jupyter notebooks
├── outputs/            # 输出文件目录
├── requirements.txt    # 核心依赖
├── requirements-dev.txt # 开发依赖
└── .gitignore          # Git 忽略文件
```

## 🎨 配置选项

### CUDA 版本

支持以下 CUDA 版本：
- `auto` - 自动检测（推荐）
- `cpu` - 仅 CPU 版本
- `11.8` - CUDA 11.8
- `12.1` - CUDA 12.1
- `12.4` - CUDA 12.4
- `none` - 不安装 CUDA 相关包

### Python 版本

```bash
mlsetup create my-project --python 3.11
```

支持的 Python 版本：3.10, 3.11, 3.12

## 🆚 与其他工具对比

| 特性 | ML Easy Setup | conda | poetry | venv |
|------|---------------|-------|--------|------|
| 专为 ML 设计 | ✅ | ✅ | ❌ | ❌ |
| 自动 CUDA 检测 | ✅ | ❌ | ❌ | ❌ |
| 安装速度 | ⚡⚡⚡ | ⚡ | ⚡⚡ | ⚡ |
| 学习曲线 | 低 | 中 | 高 | 低 |
| 预配置模板 | ✅ (13种) | ❌ | ❌ | ❌ |

## 📚 常见使用场景

### Kaggle 竞赛
```bash
mlsetup create kaggle-titanic --template gradient-boosting --cuda cpu
```

### 论文实验
```bash
mlsetup create paper-exp --template model-builder --cuda auto
```

### 数据分析报告
```bash
mlsetup create sales-analysis --template data-science --cuda cpu
```

### NLP 大模型微调
```bash
mlsetup create llm-finetune --template nlp --cuda auto
```

### 模型部署
```bash
mlsetup create model-api --template mlops --cuda cpu
```

## 🔮 路线图

- [ ] 支持 Docker 容器化环境
- [ ] 环境导出/导入功能
- [ ] 云端环境配置（AWS/GCP）
- [ ] 图形化配置界面
- [ ] 环境健康检查工具

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [uv](https://github.com/astral-sh/uv) - 高性能 Python 包管理器
- [click](https://click.palletsprojects.com/) - 优雅的命令行界面
- [rich](https://rich.readthedocs.io/) - 终端美化输出

---

⭐ 如果这个项目对您有帮助，请考虑给我们一个星标！

Made with ❤️ for the ML community
