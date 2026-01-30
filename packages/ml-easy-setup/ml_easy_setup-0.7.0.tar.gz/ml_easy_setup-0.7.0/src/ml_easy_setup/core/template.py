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
    # ===== LLM/GenAI 专用模板 =====
    "llm": {
        "type": "pytorch",
        "description": "大语言模型微调环境 - 包含 Transformers、PEFT、bitsandbytes、Flash Attention 支持",
        "core_packages": ["torch", "transformers", "peft", "accelerate", "bitsandbytes"],
        "dependencies": [
            # 基础
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scipy>=1.10.0",
            "scikit-learn>=1.3.0",
            # 深度学习框架
            "torch>=2.1.0",
            # Transformers 生态
            "transformers>=4.35.0",
            "datasets>=2.14.0",
            "tokenizers>=0.15.0",
            "evaluate>=0.4.0",
            # 加速与量化
            "accelerate>=0.25.0",
            "bitsandbytes>=0.41.0",
            # 参数高效微调
            "peft>=0.7.0",
            # Flash Attention (可选，需要兼容 GPU)
            # "flash-attn>=2.3.0",  # 需要手动安装，取决于 GPU 架构
            # 训练工具
            "trl>=0.7.0",  # Transformer Reinforcement Learning
            "deepspeed>=0.12.0",  # 分布式训练
            # 可视化
            "tensorboard>=2.15.0",
            "wandb>=0.16.0",
            "matplotlib>=3.7.0",
            "tqdm>=4.65.0",
            # 工具
            "jupyter>=1.0.0",
            "ipywidgets>=8.1.0",
            "python-dotenv>=1.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
        "flash_attention_supported": True,  # 标记此模板支持 Flash Attention
        "flash_attention_hints": """
Flash Attention 安装提示:

Flash Attention 需要兼容的 GPU 架构:
- NVIDIA Ampere (A100, A30, A40, RTX 3090, 3080, 3070) 或更新架构
- Compute Capability >= 8.0

安装方法:
pip install flash-attn --no-build-isolation

或者从预编译 wheel 安装:
pip install flash-attn==2.5.8 --find-links https://github.com/Dao-AILab/flash-attention/releases

检测 GPU 兼容性:
nvidia-smi --query-gpu=compute_cap --format=csv
""",
    },
    "rag": {
        "type": "pytorch",
        "description": "检索增强生成 (RAG) 环境 - LangChain/LlamaIndex + 向量数据库",
        "core_packages": ["langchain", "chromadb", "sentence-transformers"],
        "dependencies": [
            # 基础
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            # 深度学习
            "torch>=2.0.0",
            "transformers>=4.35.0",
            # RAG 框架 (二选一或都装)
            "langchain>=0.1.0",
            "langchain-community>=0.0.10",
            "langchain-openai>=0.0.2",
            "llama-index>=0.9.0",
            # 向量数据库
            "chromadb>=0.4.0",
            "faiss-cpu>=1.7.4",  # 或 faiss-gpu for GPU
            "qdrant-client>=1.7.0",
            # 文档处理
            "pypdf>=3.17.0",
            "pdfplumber>=0.10.0",
            "python-docx>=1.1.0",
            "beautifulsoup4>=4.12.0",
            "unstructured>=0.11.0",
            # 文本嵌入
            "sentence-transformers>=2.2.0",
            " InstructorEmbedding>=1.0.1",
            # 向量存储
            "pymongo>=4.6.0",
            "redis>=5.0.0",
            # API 和工具
            "openai>=1.10.0",
            "anthropic>=0.18.0",
            "cohere>=5.0.0",
            "requests>=2.31.0",
            "httpx>=0.26.0",
            # 可视化和工具
            "jupyter>=1.0.0",
            "tqdm>=4.65.0",
            "python-dotenv>=1.0.0",
            # Rank 检索
            "rank-bm25>=0.2.2",
            "cohere>=5.0.0",
        ],
        "dev_dependencies": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
        "rag_frameworks": {
            "langchain": "生产级 RAG 框架，丰富的集成",
            "llama-index": "专注于索引优化的 RAG 框架",
        },
        "vector_dbs": {
            "chromadb": "开源向量数据库，易用性强",
            "faiss": "Meta 开源，性能优异",
            "qdrant": "高性能向量搜索引擎",
        },
    },
    "inference": {
        "type": "pytorch",
        "description": "LLM 推理服务环境 - vLLM 高性能推理 + FastAPI 服务框架",
        "core_packages": ["vllm", "transformers", "fastapi", "uvicorn"],
        "dependencies": [
            # 基础
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            # 深度学习
            "torch>=2.1.0",
            "transformers>=4.35.0",
            # 高性能推理引擎
            "vllm>=0.4.0",  # PagedAttention，高吞吐量推理
            # 注意: TGI (text-generation-inference) 是 Docker 服务，不是 PyPI 包
            # 使用: docker run --gpus all -p 8080:80 ghcr.io/huggingface/text-generation-inference:latest
            # API 服务
            "fastapi>=0.109.0",
            "uvicorn>=0.27.0",
            "pydantic>=2.5.0",
            "pydantic-settings>=2.1.0",
            # HTTP 客户端
            "httpx>=0.26.0",
            "requests>=2.31.0",
            "aiohttp>=3.9.0",
            # 量化推理 (可选，根据需要安装)
            # "auto-gptq>=0.7.0",  # 需要 CUDA
            # "awq>=0.2.0",  # 需要 CUDA
            "bitsandbytes>=0.41.0",
            # 监控和日志
            "prometheus-client>=0.19.0",
            "opentelemetry-api>=1.22.0",
            "opentelemetry-sdk>=1.22.0",
            # 工具
            "tqdm>=4.65.0",
            "python-dotenv>=1.0.0",
            "click>=8.1.0",
            "rich>=13.7.0",
        ],
        "dev_dependencies": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.23.0",
            "httpx>=0.26.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
        "inference_engines": {
            "vllm": "PagedAttention 技术，高吞吐量推理",
            "tgi_docker": "HuggingFace 官方 Docker 推理服务: ghcr.io/huggingface/text-generation-inference",
        },
        "tgi_hints": """
TGI (Text Generation Inference) 安装提示:

TGI 不是 Python 包，需要通过 Docker 运行:

docker run --gpus all -p 8080:80 \\
  -v $PWD/models:/data \\
  ghcr.io/huggingface/text-generation-inference:latest \\
  --model-id /data/model_name

然后通过 API 访问:
curl 127.0.0.1:8080/generate \\
  -X POST \\
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":20}}'
""",
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

# ROCm 版本映射 (AMD GPU)
ROCM_VERSION_MAP = {
    "5.7": {
        "torch": "torch>=2.3.0+rocm5.7",
        "torchvision": "torchvision>=0.18.0+rocm5.7",
        "url": "https://download.pytorch.org/whl/rocm5.7",
    },
    "5.6": {
        "torch": "torch>=2.1.0+rocm5.6",
        "torchvision": "torchvision>=0.16.0+rocm5.6",
        "url": "https://download.pytorch.org/whl/rocm5.6",
    },
    "5.5": {
        "torch": "torch>=2.1.0+rocm5.5",
        "torchvision": "torchvision>=0.16.0+rocm5.5",
        "url": "https://download.pytorch.org/whl/rocm5.5",
    },
    "5.4": {
        "torch": "torch>=2.0.0+rocm5.4",
        "torchvision": "torchvision>=0.15.0+rocm5.4",
        "url": "https://download.pytorch.org/whl/rocm5.4",
    },
}

# ROCm 兼容的 PyTorch 版本 (默认使用最新稳定版)
ROCM_DEFAULT_VERSION = "5.7"


class TemplateManager:
    """模板管理器"""

    def __init__(self, template_dir: Path | None = None):
        self.template_dir = template_dir or Path(__file__).parent.parent / "templates"

    def load_template(
        self,
        name: str,
        cuda_version: str = "none",
        use_rocm: bool = False,
        rocm_version: str | None = None
    ) -> Dict[str, Any]:
        """
        加载模板配置

        Args:
            name: 模板名称
            cuda_version: CUDA 版本 (none, 11.8, 12.1, 12.4)
            use_rocm: 是否使用 ROCm (AMD GPU)
            rocm_version: ROCm 版本 (5.4, 5.5, 5.6, 5.7)

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

        # 应用 CUDA 或 ROCm 配置
        if use_rocm and config["type"] == "pytorch":
            config = self._apply_rocm_config(config, rocm_version or ROCM_DEFAULT_VERSION)
        elif cuda_version != "none" and config["type"] in ["pytorch", "tensorflow"]:
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

    def _apply_rocm_config(self, config: Dict[str, Any], rocm_version: str) -> Dict[str, Any]:
        """应用 ROCm 配置到模板"""
        import copy

        config = copy.deepcopy(config)

        if rocm_version in ROCM_VERSION_MAP:
            # 获取 ROCm 特定的 PyTorch 版本
            rocm_config = ROCM_VERSION_MAP[rocm_version]

            # 更新依赖列表，替换 torch 和 torchvision
            new_deps = []
            for dep in config.get("dependencies", []):
                if dep.startswith("torch>="):
                    new_deps.append(rocm_config["torch"])
                elif dep.startswith("torchvision>="):
                    new_deps.append(rocm_config.get("torchvision", "torchvision>=0.15.0"))
                else:
                    new_deps.append(dep)

            config["dependencies"] = new_deps
            config["rocm_version"] = rocm_version
            config["install_hints"] = self._get_rocm_install_hints(rocm_version, rocm_config["url"])

        return config

    def _get_rocm_install_hints(self, rocm_version: str, wheel_url: str) -> str:
        """获取 ROCm 安装提示"""
        return f"""
注意: ROCm {rocm_version} 支持 (AMD GPU):

1. 确保 ROCm 已正确安装:
   - 检查: rocm-smi --showversion
   - 下载: https://rocm.docs.amd.com/

2. PyTorch ROCm 版本将从官方 wheel 安装:
   {wheel_url}

3. 如果安装遇到问题:
   - 检查 GPU 架构兼容性 (gfx900/gfx906/gfx1030+)
   - 确保 ROCm 版本与 PyTorch 版本匹配
   - 参考: https://pytorch.org/get-started/locally/

推荐 AMD GPU:
- RX 6000/7000 系列 ( gfx1030+ )
- MI 系列 (计算卡)
- Vega 系列 ( gfx900 )
"""

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
