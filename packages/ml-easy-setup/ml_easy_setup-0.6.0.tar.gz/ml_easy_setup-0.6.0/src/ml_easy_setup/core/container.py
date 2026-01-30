"""
容器配置生成器 - 负责生成 Dockerfile 和 DevContainer 配置
"""

from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from rich.console import Console

console = Console()


@dataclass
class ContainerConfig:
    """容器配置"""
    project_name: str
    template_type: str  # "pytorch", "tensorflow", "minimal"
    cuda_version: Optional[str]  # "11.8", "12.1", "12.4", "cpu"
    python_version: str
    dependencies: list[str]
    include_devcontainer: bool = False


class ContainerManager:
    """容器管理器 - 生成 Dockerfile 和 DevContainer 配置"""

    # CUDA 基础镜像映射
    CUDA_BASE_IMAGES = {
        "11.8": "nvidia/cuda:11.8.0-runtime-ubuntu22.04",
        "12.1": "nvidia/cuda:12.1.0-runtime-ubuntu22.04",
        "12.4": "nvidia/cuda:12.4.0-runtime-ubuntu22.04",
        "cpu": "python:3.10-slim",
        "none": "python:3.10-slim",
    }

    # PyTorch CUDA 索引 URL
    PYTORCH_INDEX_URLS = {
        "11.8": "https://download.pytorch.org/whl/cu118",
        "12.1": "https://download.pytorch.org/whl/cu121",
        "12.4": "https://download.pytorch.org/whl/cu124",
    }

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def generate_dockerfile(self, config: ContainerConfig) -> None:
        """生成 Dockerfile"""
        dockerfile_path = self.project_path / "Dockerfile"

        content = self._generate_dockerfile_content(config)
        dockerfile_path.write_text(content)

        console.print(f"   [dim]生成 Dockerfile: {dockerfile_path}[/dim]")

    def generate_devcontainer(self, config: ContainerConfig) -> None:
        """生成 .devcontainer 配置"""
        devcontainer_path = self.project_path / ".devcontainer"
        devcontainer_path.mkdir(parents=True, exist_ok=True)

        # 生成 devcontainer.json
        devcontainer_json = devcontainer_path / "devcontainer.json"
        content = self._generate_devcontainer_content(config)
        devcontainer_json.write_text(content)

        # 生成 docker-compose.yml (用于多容器支持)
        docker_compose = devcontainer_path / "docker-compose.yml"
        compose_content = self._generate_docker_compose_content(config)
        docker_compose.write_text(compose_content)

        console.print(f"   [dim]生成 .devcontainer 配置: {devcontainer_path}[/dim]")

    def _get_base_image(self, config: ContainerConfig) -> str:
        """获取基础镜像"""
        if config.cuda_version in ["cpu", "none"]:
            return f"python:{config.python_version}-slim"
        return self.CUDA_BASE_IMAGES.get(config.cuda_version, "python:3.10-slim")

    def _get_pytorch_index_url(self, config: ContainerConfig) -> Optional[str]:
        """获取 PyTorch 索引 URL"""
        if config.cuda_version in ["cpu", "none"]:
            return None
        return self.PYTORCH_INDEX_URLS.get(config.cuda_version)

    def _generate_dockerfile_content(self, config: ContainerConfig) -> str:
        """生成 Dockerfile 内容"""
        base_image = self._get_base_image(config)
        pytorch_url = self._get_pytorch_index_url(config)

        # 构建依赖安装命令
        deps_str = " \\\n    ".join([f'"{dep}"' for dep in config.dependencies])

        # 多阶段构建
        if config.cuda_version not in ["cpu", "none"]:
            return self._generate_cuda_dockerfile(config, base_image, pytorch_url, deps_str)
        else:
            return self._generate_cpu_dockerfile(config, base_image, deps_str)

    def _generate_cuda_dockerfile(
        self,
        config: ContainerConfig,
        base_image: str,
        pytorch_url: Optional[str],
        deps_str: str
    ) -> str:
        """生成 CUDA 版本的 Dockerfile"""
        pytorch_install = ""
        if config.template_type == "pytorch" and pytorch_url:
            pytorch_install = f"""
# 安装 PyTorch (CUDA 版本)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url {pytorch_url}
"""

        deps_install = ""
        if config.dependencies:
            filtered_deps = [d for d in config.dependencies if not d.startswith("torch")]
            if filtered_deps:
                deps_str = " \\\n    ".join([f'"{dep}"' for dep in filtered_deps])
                deps_install = f"""
# 安装项目依赖
RUN pip install --no-cache-dir {deps_str}
"""

        return f"""# 多阶段构建 - 优化镜像大小
FROM {base_image} AS builder

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PIP_NO_CACHE_DIR=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    git \\
    wget \\
    curl \\
    vim \\
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 升级 pip 和安装构建工具
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 安装 uv (可选，用于更快的依赖安装)
RUN pip install --no-cache-dir uv
{pytorch_install}
{deps_install}
# 最终阶段
FROM {base_image}

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PIP_NO_CACHE_DIR=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \\
    libgomp1 \\
    libglib2.0-0 \\
    libsm6 \\
    libxext6 \\
    libxrender-dev \\
    libgl1-mesa-glx \\
    git \\
    wget \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 设置工作目录
WORKDIR /workspace

# 复制项目文件
COPY requirements.txt ./
COPY src/ ./src/
COPY data/ ./data/

# 暴露常用端口 (Jupyter, TensorBoard, API)
EXPOSE 8888 6006 8000

# 默认命令
CMD ["python", "-u", "src/main.py"]
"""

    def _generate_cpu_dockerfile(
        self,
        config: ContainerConfig,
        base_image: str,
        deps_str: str
    ) -> str:
        """生成 CPU 版本的 Dockerfile"""
        deps_install = ""
        if config.dependencies:
            deps_install = f"""
# 安装项目依赖
RUN pip install --no-cache-dir {deps_str}
"""

        return f"""# 基础镜像
FROM {base_image}

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PIP_NO_CACHE_DIR=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    git \\
    wget \\
    curl \\
    vim \\
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
{deps_install}
# 创建工作目录
WORKDIR /workspace

# 复制项目文件
COPY requirements.txt ./
COPY src/ ./src/
COPY data/ ./data/

# 暴露常用端口
EXPOSE 8888 6006 8000

# 默认命令
CMD ["python", "-u", "src/main.py"]
"""

    def _generate_devcontainer_content(self, config: ContainerConfig) -> str:
        """生成 .devcontainer/devcontainer.json 内容"""
        cuda_support = config.cuda_version not in ["cpu", "none"]

        # 根据模板类型配置端口
        ports = []
        if config.template_type in ["pytorch", "tensorflow"]:
            ports.extend([
                "8888:8888",  # Jupyter
                "6006:6006",  # TensorBoard
            ])
        if config.template_type == "mlops":
            ports.append("8000:8000")  # FastAPI

        devcontainer_config = {
            "name": f"{config.project_name} ({config.template_type})",
            "dockerFile": "Dockerfile",
            "build": {
                "context": "..",
                "dockerfile": "Dockerfile"
            },
            "customizations": {
                "vscode": {
                    "extensions": [
                        "ms-python.python",
                        "ms-python.vscode-pylance",
                        "ms-python.black-formatter",
                        "ms-python.ruff",
                        "ms-toolsai.jupyter",
                    ]
                }
            },
            "forwardPorts": ports,
            "portsAttributes": {
                "8888": {"label": "Jupyter", "onAutoForward": "notify"},
                "6006": {"label": "TensorBoard", "onAutoForward": "notify"},
                "8000": {"label": "API Server", "onAutoForward": "notify"},
            },
            "mounts": [
                "source=${{localWorkspaceFolder}}/../data,target=/workspace/data,type=bind,consistency=cached",
                "source=${{localWorkspaceFolder}}/../outputs,target=/workspace/outputs,type=bind,consistency=cached",
            ],
            "postCreateCommand": "pip install -e . && echo '✓ DevContainer 环境就绪'",
            "remoteUser": "vscode",
            "features": {},
        }

        # CUDA 特定配置
        if cuda_support:
            devcontainer_config["features"] = {
                "ghcr.io/devcontainers/features/nvidia-cuda:1": {
                    "installCudnn": true,
                    "installToolkit": true,
                    "version": config.cuda_version,
                }
            }
            devcontainer_config["runArgs"] = [
                "--gpus=all",
                "--shm-size=16g",
                "--ulimit=memlock=-1",
                "--ulimit=stack=67108864",
            ]

        import json
        return json.dumps(devcontainer_config, indent=2, ensure_ascii=False)

    def _generate_docker_compose_content(self, config: ContainerConfig) -> str:
        """生成 docker-compose.yml 内容"""
        services = {
            "app": {
                "build": {
                    "context": "..",
                    "dockerfile": "Dockerfile"
                },
                "volumes": [
                    "../..:/workspaces/${{localWorkspaceFolderBasename}}:cached",
                    "../../data:/workspace/data:cached",
                    "../../outputs:/workspace/outputs:cached",
                ],
                "command": "sleep infinity",
                "networks": ["ml-network"],
            }
        }

        # CUDA 特定配置
        if config.cuda_version not in ["cpu", "none"]:
            services["app"]["deploy"] = {
                "resources": {
                    "reservations": {
                        "devices": [
                            {
                                "driver": "nvidia",
                                "count": "all",
                                "capabilities": ["gpu"],
                            }
                        ]
                    }
                }
            }
            services["app"]["shm_size"] = "16g"

        # 添加 TensorBoard 服务 (PyTorch/TensorFlow 模板)
        if config.template_type in ["pytorch", "tensorflow", "nlp", "cv", "full"]:
            services["tensorboard"] = {
                "image": "tensorflow/tensorflow:latest",
                "command": "tensorboard --logdir=/workspace/outputs --host=0.0.0.0 --port=6006",
                "volumes": ["../../outputs:/workspace/outputs:cached"],
                "ports": ["6006:6006"],
                "networks": ["ml-network"],
            }

        compose_config = {
            "version": "3.8",
            "services": services,
            "networks": {"ml-network": {"driver": "bridge"}},
        }

        import yaml
        return yaml.dump(compose_config, default_flow_style=False, allow_unicode=True)

    def generate_dockerignore(self) -> None:
        """生成 .dockerignore 文件"""
        content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp

# Git
.git/
.gitignore

# ML Artifacts (keep directories)
outputs/*
!outputs/.gitkeep
checkpoints/*
!checkpoints/.gitkeep
models/*
!models/.gitkeep

# Documentation
*.md
docs/

# Container (don't nest containers)
.docker/
Dockerfile
.dockerignore
docker-compose.yml

# Test
.pytest_cache/
.coverage
htmlcov/
tests/
"""
        (self.project_path / ".dockerignore").write_text(content)
        console.print(f"   [dim]生成 .dockerignore[/dim]")

    def generate_readme_addon(self, config: ContainerConfig) -> None:
        """生成容器使用说明的 README 附录"""
        readme_path = self.project_path / "README_CONTAINER.md"

        cuda_section = ""
        if config.cuda_version not in ["cpu", "none"]:
            cuda_section = f"""
## CUDA 支持

此项目配置了 CUDA {config.cuda_version} 支持。确保宿主机安装了:

1. **NVIDIA Driver** (版本 >= 470.42.01 for CUDA 11.8)
2. **NVIDIA Container Toolkit** (nvidia-docker2)

```bash
# 安装 NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

3. **验证 GPU 支持**
```bash
docker run --rm --gpus all nvidia/cuda:{config.cuda_version}-base-ubuntu22.04 nvidia-smi
```
"""

        devcontainer_section = ""
        if config.include_devcontainer:
            devcontainer_section = """
## 使用 VS Code DevContainer

1. 安装 [Dev Container 扩展](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. 按 `F1` → 选择 `Dev Containers: Reopen in Container`
3. 等待容器构建完成

**特性**:
- 完整的 Python 开发环境
- 预装的 VS Code 扩展 (Python, Pylance, Jupyter, Black, Ruff)
- 自动端口转发 (Jupyter: 8888, TensorBoard: 6006, API: 8000)
- 持久化数据卷挂载
"""

        content = f"""# 容器化部署指南

## Docker 构建

### 构建镜像
```bash
docker build -t {config.project_name}:latest .
```

### 运行容器

**CPU 模式**:
```bash
docker run -it --rm -p 8888:8888 {config.project_name}:latest
```

**GPU 模式** (需要 NVIDIA Container Toolkit):
```bash
docker run -it --rm --gpus all -p 8888:8888 {config.project_name}:latest
```

### 挂载数据目录
```bash
docker run -it --rm \\
  -v $(pwd)/data:/workspace/data \\
  -v $(pwd)/outputs:/workspace/outputs \\
  -p 8888:8888 \\
  {config.project_name}:latest
```

### 交互式开发
```bash
# 启动容器并进入 bash
docker run -it --rm -v $(pwd):/workspace -p 8888:8888 {config.project_name}:latest bash

# 在容器内运行
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

### 启动 Jupyter Lab
```bash
docker run -it --rm \\
  -v $(pwd):/workspace \\
  -p 8888:8888 \\
  {config.project_name}:latest \\
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=''
```
{cuda_section}{devcontainer_section}
## Docker Compose (推荐用于开发)

使用 `.devcontainer/docker-compose.yml`:

```bash
# 启动服务
cd .devcontainer
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 环境变量

可以在运行时覆盖环境变量:

```bash
docker run -it --rm \\
  -e PYTHONPATH=/workspace/src \\
  -e CUDA_VISIBLE_DEVICES=0 \\
  {config.project_name}:latest
```

## 故障排查

### GPU 不可用
```bash
# 检查宿主机 GPU
nvidia-smi

# 检查 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:base nvidia-smi
```

### 镜像体积过大
```bash
# 查看镜像大小
docker images {config.project_name}

# 使用多阶段构建 (已实现) 减小镜像体积
# 清理未使用的镜像
docker system prune -a
```
"""

        readme_path.write_text(content)
        console.print(f"   [dim]生成容器使用指南: README_CONTAINER.md[/dim]")
