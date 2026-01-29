"""
模板管理器 - 管理预配置的环境模板
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any

# 模板内置配置（作为默认值）
BUILTIN_TEMPLATES = {
    "minimal": {
        "type": "minimal",
        "description": "最小化配置，仅包含基础 ML 库",
        "core_packages": ["numpy", "pandas", "scikit-learn"],
        "dependencies": [
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scikit-learn>=1.3.0",
            "matplotlib>=3.7.0",
            "jupyter>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    "pytorch": {
        "type": "pytorch",
        "description": "PyTorch 深度学习框架配置",
        "core_packages": ["torch", "torchvision", "torchaudio"],
        "dependencies": [
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "torchaudio>=2.0.0",
            "matplotlib>=3.7.0",
            "tensorboard>=2.13.0",
            "tqdm>=4.65.0",
            "pillow>=9.5.0",
            "scikit-learn>=1.3.0",
            "jupyter>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    "tensorflow": {
        "type": "tensorflow",
        "description": "TensorFlow 深度学习框架配置",
        "core_packages": ["tensorflow", "keras"],
        "dependencies": [
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "tensorflow>=2.13.0",
            "matplotlib>=3.7.0",
            "tensorboard>=2.13.0",
            "tqdm>=4.65.0",
            "pillow>=9.5.0",
            "scikit-learn>=1.3.0",
            "jupyter>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    "nlp": {
        "type": "pytorch",
        "description": "自然语言处理环境 (基于 PyTorch + Transformers)",
        "core_packages": ["torch", "transformers", "datasets"],
        "dependencies": [
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "torch>=2.0.0",
            "transformers>=4.30.0",
            "datasets>=2.12.0",
            "tokenizers>=0.13.0",
            "accelerate>=0.20.0",
            "evaluate>=0.4.0",
            "scikit-learn>=1.3.0",
            "matplotlib>=3.7.0",
            "tensorboard>=2.13.0",
            "tqdm>=4.65.0",
            "jupyter>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    "cv": {
        "type": "pytorch",
        "description": "计算机视觉环境 (基于 PyTorch + torchvision)",
        "core_packages": ["torch", "torchvision", "opencv-python"],
        "dependencies": [
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "opencv-python>=4.7.0",
            "pillow>=9.5.0",
            "albumentations>=1.3.0",
            "scikit-learn>=1.3.0",
            "scikit-image>=0.21.0",
            "matplotlib>=3.7.0",
            "tensorboard>=2.13.0",
            "tqdm>=4.65.0",
            "jupyter>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    "rl": {
        "type": "pytorch",
        "description": "强化学习环境 (PyTorch + Gym + Stable-Baselines3)",
        "core_packages": ["torch", "gymnasium", "stable-baselines3"],
        "dependencies": [
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "torch>=2.0.0",
            "gymnasium>=0.28.0",
            "stable-baselines3>=2.0.0",
            "shimmy>=0.2.0",
            "matplotlib>=3.7.0",
            "tensorboard>=2.13.0",
            "tqdm>=4.65.0",
            "scikit-learn>=1.3.0",
            "pillow>=9.5.0",
            "opencv-python>=4.7.0",
            "moviepy>=1.0.3",
            "jupyter>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    # ===== 新增模板 =====
    "model-builder": {
        "type": "minimal",
        "description": "模型构建环境 - 包含超参数优化、实验跟踪、模型管理等工具",
        "core_packages": ["scikit-learn", "optuna", "mlflow", "xgboost"],
        "dependencies": [
            # 基础
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scipy>=1.10.0",
            "scikit-learn>=1.3.0",
            # 模型库
            "xgboost>=2.0.0",
            "lightgbm>=4.0.0",
            "catboost>=1.2.0",
            # 超参数优化
            "optuna>=3.3.0",
            "optuna-integration>=3.3.0",
            "hyperopt>=0.2.7",
            # 实验跟踪
            "mlflow>=2.9.0",
            "wandb>=0.15.0",
            # 可视化
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "plotly>=5.17.0",
            # 工具
            "tqdm>=4.65.0",
            "joblib>=1.3.0",
            "ipywidgets>=8.1.0",
            "jupyter>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "pytest-cov>=4.1.0",
        ],
    },
    "algorithm-validator": {
        "type": "minimal",
        "description": "算法验证环境 - 包含测试框架、基准测试、数据集和评估工具",
        "core_packages": ["pytest", "scikit-learn", "datasets", "evaluate"],
        "dependencies": [
            # 基础
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scikit-learn>=1.3.0",
            # 测试框架
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-xdist>=3.3.0",
            "pytest-benchmark>=4.0.0",
            # 数据集
            "datasets>=2.14.0",
            "scikit-dataset>=0.1.0",
            # 评估工具
            "evaluate>=0.4.0",
            "scoring>=0.1.0",
            # 基准测试
            "memory-profiler>=0.61.0",
            "psutil>=5.9.0",
            # 可视化
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            # 报告
            "jupyter>=1.0.0",
            "ipython>=8.14.0",
        ],
        "dev_dependencies": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.5.0",
        ],
    },
    "data-science": {
        "type": "minimal",
        "description": "数据科学环境 - 数据处理、可视化、统计分析完整工具链",
        "core_packages": ["pandas", "numpy", "matplotlib", "seaborn", "plotly"],
        "dependencies": [
            # 核心
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scipy>=1.10.0",
            # 数据处理
            "polars>=0.19.0",
            "pyarrow>=12.0.0",
            "dask>=2023.8.0",
            # 可视化
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "plotly>=5.17.0",
            "altair>=5.0.0",
            "bokeh>=3.2.0",
            # 统计分析
            "statsmodels>=0.14.0",
            "scikit-learn>=1.3.0",
            # 交互式
            "jupyter>=1.0.0",
            "ipywidgets>=8.1.0",
            "ipython>=8.14.0",
            "notebook>=7.0.0",
            # 工具
            "tqdm>=4.65.0",
            "python-dotenv>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    "gradient-boosting": {
        "type": "minimal",
        "description": "梯度提升环境 - XGBoost、LightGBM、CatBoost 专用环境",
        "core_packages": ["xgboost", "lightgbm", "catboost"],
        "dependencies": [
            # 基础
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scipy>=1.10.0",
            "scikit-learn>=1.3.0",
            # 梯度提升库
            "xgboost>=2.0.0",
            "lightgbm>=4.0.0",
            "catboost>=1.2.0",
            "ngboost>=0.4.0",
            # 优化
            "optuna>=3.3.0",
            # 可视化
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "shap>=0.42.0",
            # 工具
            "tqdm>=4.65.0",
            "joblib>=1.3.0",
            "jupyter>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    "mlops": {
        "type": "minimal",
        "description": "MLOps 环境 - 模型部署、监控、版本管理完整工具链",
        "core_packages": ["mlflow", "bentoml", "fastapi"],
        "dependencies": [
            # 基础
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scikit-learn>=1.3.0",
            # 模型服务
            "bentoml>=1.0.0",
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            # 模型管理
            "mlflow>=2.9.0",
            "dvc>=3.0.0",
            # 监控
            "prometheus-client>=0.17.0",
            "opencensus>=0.11.0",
            # API 工具
            "pydantic>=2.0.0",
            "pydantic-settings>=2.0.0",
            "httpx>=0.24.0",
            # 容器化
            "docker>=6.1.0",
            # CI/CD
            "click>=8.1.0",
            "rich>=13.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "httpx>=0.24.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    "timeseries": {
        "type": "minimal",
        "description": "时间序列分析环境 - Prophet、statsmodels、darts 等时间序列工具",
        "core_packages": ["prophet", "statsmodels", "darts"],
        "dependencies": [
            # 基础
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scipy>=1.10.0",
            # 时间序列库
            "prophet>=2.0.0",
            "statsmodels>=0.14.0",
            "darts>=0.24.0",
            "sktime>=0.23.0",
            "tslearn>=0.6.0",
            # 机器学习
            "scikit-learn>=1.3.0",
            "xgboost>=2.0.0",
            # 可视化
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "plotly>=5.17.0",
            # 工具
            "tqdm>=4.65.0",
            "jupyter>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    "graph": {
        "type": "pytorch",
        "description": "图学习环境 - PyG (PyTorch Geometric)、DGL 图神经网络",
        "core_packages": ["torch", "torch-geometric", "dgl"],
        "dependencies": [
            # 基础
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scipy>=1.10.0",
            "torch>=2.0.0",
            # 图学习库
            "torch-geometric>=2.3.0",
            "dgl>=1.1.0",
            "networkx>=3.1.0",
            "ogb>=1.3.6",
            # 机器学习
            "scikit-learn>=1.3.0",
            # 可视化
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "plotly>=5.17.0",
            # 工具
            "tqdm>=4.65.0",
            "jupyter>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    "full": {
        "type": "minimal",
        "description": "完整环境 - 包含所有常用 ML/DL 工具（适用于需要完整工具链的场景）",
        "core_packages": ["numpy", "pandas", "scikit-learn", "torch", "tensorflow"],
        "dependencies": [
            # 基础科学计算
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scipy>=1.10.0",
            # 深度学习
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "tensorflow>=2.13.0",
            # 传统 ML
            "scikit-learn>=1.3.0",
            "xgboost>=2.0.0",
            "lightgbm>=4.0.0",
            "catboost>=1.2.0",
            # NLP
            "transformers>=4.30.0",
            "datasets>=2.12.0",
            # CV
            "opencv-python>=4.7.0",
            "pillow>=9.5.0",
            # 强化学习
            "gymnasium>=0.28.0",
            "stable-baselines3>=2.0.0",
            # 可视化
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "plotly>=5.17.0",
            # 工具
            "tqdm>=4.65.0",
            "tensorboard>=2.13.0",
            "jupyter>=1.0.0",
            # MLOps
            "mlflow>=2.9.0",
            "wandb>=0.15.0",
            "optuna>=3.3.0",
        ],
        "dev_dependencies": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "pytest-cov>=4.1.0",
            "mypy>=1.5.0",
        ],
    },
}

# CUDA 版本映射
CUDA_VERSION_MAP = {
    "11.8": {
        "torch": "torch>=2.0.0",
        "tensorflow": "tensorflow[and-cuda]>=2.13.0",
    },
    "12.1": {
        "torch": "torch>=2.0.0",
        "tensorflow": "tensorflow[and-cuda]>=2.15.0",
    },
    "12.4": {
        "torch": "torch>=2.2.0",
        "tensorflow": "tensorflow[and-cuda]>=2.16.0",
    },
    "none": {
        "torch": "torch>=2.0.0+cpu",
        "tensorflow": "tensorflow>=2.13.0",
    },
}


class TemplateManager:
    """模板管理器"""

    def __init__(self, template_dir: Path | None = None):
        self.template_dir = template_dir or Path(__file__).parent.parent / "templates"

    def load_template(self, name: str, cuda_version: str = "none") -> Dict[str, Any]:
        """
        加载模板配置

        Args:
            name: 模板名称
            cuda_version: CUDA 版本 (none, 11.8, 12.1, 12.4)

        Returns:
            模板配置字典
        """
        # 首先尝试从文件加载
        template_file = self.template_dir / f"{name}.yaml"
        if template_file.exists():
            with open(template_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        else:
            # 使用内置模板
            config = BUILTIN_TEMPLATES.get(name, BUILTIN_TEMPLATES["minimal"])

        # 应用 CUDA 配置
        if cuda_version != "none" and config["type"] in ["pytorch", "tensorflow"]:
            config = self._apply_cuda_config(config, cuda_version)

        return config

    def _apply_cuda_config(self, config: Dict[str, Any], cuda_version: str) -> Dict[str, Any]:
        """应用 CUDA 配置到模板"""
        import copy

        config = copy.deepcopy(config)
        framework_type = config["type"]

        if framework_type in CUDA_VERSION_MAP.get(cuda_version, {}):
            # 添加 CUDA 安装提示
            config["cuda_version"] = cuda_version
            config["install_hints"] = self._get_cuda_install_hints(cuda_version)

        return config

    def _get_cuda_install_hints(self, cuda_version: str) -> str:
        """获取 CUDA 安装提示"""
        return f"""
注意: CUDA {cuda_version} 支持需要:

1. 确保 GPU 驱动已正确安装
2. 对于 PyTorch，可能需要从官网安装特定版本
3. 访问 https://pytorch.org 获取安装命令

如果安装过程中遇到问题，可以使用 --cuda cpu 选项安装 CPU 版本
"""

    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有可用模板"""
        templates = []

        for name, config in BUILTIN_TEMPLATES.items():
            templates.append({
                "name": name,
                "description": config["description"],
                "core_packages": config["core_packages"],
                "type": config["type"],
            })

        return templates

    def save_template(self, name: str, config: Dict[str, Any]) -> None:
        """保存自定义模板"""
        self.template_dir.mkdir(parents=True, exist_ok=True)
        template_file = self.template_dir / f"{name}.yaml"

        with open(template_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
