"""
环境管理器 - 负责创建和管理虚拟环境
"""

import subprocess
import sys
from pathlib import Path
from typing import List

from rich.console import Console

console = Console()


class EnvironmentManager:
    """环境管理器 - 封装 uv/venv 操作"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.venv_path = project_path / ".venv"

    def create_project_structure(self, name: str) -> None:
        """创建基础项目结构"""
        self.project_path.mkdir(parents=True, exist_ok=True)

        # 创建标准目录结构
        dirs = ["src", "tests", "data", "notebooks", "outputs"]
        for dir_name in dirs:
            (self.project_path / dir_name).mkdir(exist_ok=True)

        # 创建 .gitignore
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Data & Outputs
data/raw/*
data/processed/*
outputs/*
!data/.gitkeep
!outputs/.gitkeep

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints/

# ML
*.pth
*.pt
*.ckpt
*.pkl
*.h5
models/
checkpoints/

# Logs
logs/
*.log
"""
        (self.project_path / ".gitignore").write_text(gitignore_content)

        # 创建 data 和 outputs 的 .gitkeep
        (self.project_path / "data" / ".gitkeep").write_text("")
        (self.project_path / "outputs" / ".gitkeep").write_text("")

    def create_environment(
        self,
        python_version: str,
        dependencies: List[str],
        dev_dependencies: List[str]
    ) -> None:
        """创建虚拟环境并安装依赖"""
        # 检查 uv 是否可用
        uv_available = self._check_uv_available()

        if uv_available:
            self._create_with_uv(python_version, dependencies, dev_dependencies)
        else:
            self._create_with_venv(dependencies, dev_dependencies)

    def _check_uv_available(self) -> bool:
        """检查 uv 是否可用"""
        try:
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _create_with_uv(
        self,
        python_version: str,
        dependencies: List[str],
        dev_dependencies: List[str]
    ) -> None:
        """使用 uv 创建环境"""
        console.print("   [dim]使用 uv 创建环境...[/dim]")

        # 创建虚拟环境
        subprocess.run(
            ["uv", "venv", str(self.venv_path), "-p", python_version],
            check=True,
            cwd=self.project_path
        )

        # 安装核心依赖
        if dependencies:
            console.print("   [dim]安装核心依赖...[/dim]")
            subprocess.run(
                ["uv", "pip", "install"] + dependencies,
                check=True,
                cwd=self.project_path
            )

        # 安装开发依赖
        if dev_dependencies:
            console.print("   [dim]安装开发依赖...[/dim]")
            subprocess.run(
                ["uv", "pip", "install"] + dev_dependencies,
                check=True,
                cwd=self.project_path
            )

    def _create_with_venv(
        self,
        dependencies: List[str],
        dev_dependencies: List[str]
    ) -> None:
        """使用 venv 创建环境"""
        console.print("   [dim]使用 venv 创建环境...[/dim]")

        # 创建虚拟环境
        subprocess.run(
            [sys.executable, "-m", "venv", str(self.venv_path)],
            check=True,
            cwd=self.project_path
        )

        # 获取 pip 路径
        pip_path = self.venv_path / "bin" / "pip"
        if sys.platform == "win32":
            pip_path = self.venv_path / "Scripts" / "pip.exe"

        # 升级 pip
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)

        # 安装依赖
        all_deps = dependencies + dev_dependencies
        if all_deps:
            console.print("   [dim]安装依赖...[/dim]")
            subprocess.run(
                [str(pip_path), "install"] + all_deps,
                check=True
            )

    def add_packages(self, packages: List[str], dev: bool = False) -> None:
        """添加额外的包"""
        uv_available = self._check_uv_available()

        if uv_available:
            cmd = ["uv", "pip", "install"] + packages
        else:
            pip_path = self._get_pip_path()
            cmd = [str(pip_path), "install"] + packages

        subprocess.run(cmd, check=True, cwd=self.project_path)

    def _get_pip_path(self) -> Path:
        """获取 pip 可执行文件路径"""
        pip_path = self.venv_path / "bin" / "pip"
        if sys.platform == "win32":
            pip_path = self.venv_path / "Scripts" / "pip.exe"
        return pip_path

    def generate_project_files(self, name: str, template_config: dict) -> None:
        """生成项目文件"""
        # 创建 requirements.txt
        deps = template_config.get("dependencies", [])
        dev_deps = template_config.get("dev_dependencies", [])

        requirements_content = "\n".join(deps)
        (self.project_path / "requirements.txt").write_text(requirements_content)

        # 创建 requirements-dev.txt
        if dev_deps:
            dev_content = "\n".join(dev_deps)
            (self.project_path / "requirements-dev.txt").write_text(dev_content)

        # 创建示例代码
        self._create_example_code(name, template_config)

    def _create_example_code(self, name: str, template_config: dict) -> None:
        """创建示例代码文件"""
        template_type = template_config.get("type", "minimal")

        examples = {
            "pytorch": """import torch
import torch.nn as nn


def main():
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # 简单测试
    x = torch.randn(3, 4)
    print(f"\\nRandom tensor:\\n{x}")


if __name__ == "__main__":
    main()
""",
            "tensorflow": """import tensorflow as tf


def main():
    print(f"TensorFlow version: {tf.__version__}")
    print(f"GPU available: {len(tf.config.list_physical_devices('GPU')) > 0}")

    # 简单测试
    x = tf.random.normal((3, 4))
    print(f"\\nRandom tensor:\\n{x}")


if __name__ == "__main__":
    main()
""",
            "minimal": """print("Hello, ML World!")

# 这个环境已配置好基础 ML 库
# 可以开始安装你需要的包了
""",
        }

        example_code = examples.get(template_type, examples["minimal"])
        (self.project_path / "src" / "main.py").write_text(example_code)
