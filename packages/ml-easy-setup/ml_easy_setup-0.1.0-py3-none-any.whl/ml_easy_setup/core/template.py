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
