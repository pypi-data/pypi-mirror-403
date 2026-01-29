"""
环境健康检查器 - 检查环境状态并提供修复建议
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class HealthChecker:
    """环境健康检查器"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.venv_path = project_path / ".venv"
        self.issues = []
        self.warnings = []
        self.suggestions = []
        # 检测是否使用 uv
        self.use_uv = self._detect_uv()

    def _detect_uv(self) -> bool:
        """检测项目是否使用 uv"""
        try:
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def check_all(self) -> Dict[str, Any]:
        """
        执行完整健康检查

        Returns:
            检查结果字典
        """
        results = {
            "status": "healthy",
            "issues": [],
            "warnings": [],
            "suggestions": [],
            "scores": {}
        }

        # 1. 检查虚拟环境
        results["scores"]["venv"] = self._check_venv()

        # 2. 检查依赖冲突
        results["scores"]["dependencies"] = self._check_dependencies()

        # 3. 检查 CUDA/GPU
        results["scores"]["gpu"] = self._check_gpu()

        # 4. 检查包版本兼容性
        results["scores"]["compatibility"] = self._check_compatibility()

        # 5. 检查磁盘空间
        results["scores"]["disk"] = self._check_disk()

        # 汇总结果
        results["issues"] = self.issues
        results["warnings"] = self.warnings
        results["suggestions"] = self.suggestions

        # 总体状态
        if any(score < 0.5 for score in results["scores"].values()):
            results["status"] = "critical"
        elif any(score < 0.8 for score in results["scores"].values()):
            results["status"] = "warning"

        return results

    def _check_venv(self) -> float:
        """检查虚拟环境状态"""
        score = 1.0

        if not self.venv_path.exists():
            self.issues.append("虚拟环境不存在")
            self.suggestions.append("运行: mlsetup create <name> 创建新环境")
            return 0.0

        # uv 环境不需要检查 pip
        if self.use_uv:
            self.suggestions.append("✓ 使用 uv 包管理器")
        else:
            # 检查 pip (传统 venv)
            pip_path = self._get_pip_path()
            if not pip_path.exists():
                self.issues.append("pip 不可用")
                score -= 0.5
            else:
                try:
                    result = subprocess.run(
                        [str(pip_path), "--version"],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode != 0:
                        self.warnings.append("pip 可能损坏")
                        score -= 0.2
                except Exception:
                    self.warnings.append("无法检查 pip 状态")

        # 检查 requirements.txt
        req_file = self.project_path / "requirements.txt"
        if not req_file.exists():
            self.warnings.append("缺少 requirements.txt")
        else:
            try:
                with open(req_file) as f:
                    deps = f.read().strip().split('\n')
                    if len(deps) == 0 or (len(deps) == 1 and deps[0] == ''):
                        self.warnings.append("requirements.txt 为空")
            except Exception:
                pass

        return max(0.0, score)

    def _check_dependencies(self) -> float:
        """检查依赖冲突"""
        score = 1.0

        req_file = self.project_path / "requirements.txt"
        if not req_file.exists():
            self.warnings.append("无 requirements.txt，跳过依赖检查")
            return 0.8

        # 根据是否使用 uv 选择检查命令
        if self.use_uv:
            return self._check_dependencies_uv(score)
        else:
            return self._check_dependencies_pip(score)

    def _check_dependencies_uv(self, score: float) -> float:
        """使用 uv 检查依赖"""
        try:
            result = subprocess.run(
                ["uv", "pip", "check"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                # 有依赖问题
                self.warnings.append("发现依赖冲突或不兼容")
                score -= 0.3
                self.suggestions.append("运行: uv pip check 查看详细冲突信息")
                self._analyze_dependency_issues(result.stdout + result.stderr)
            else:
                self.suggestions.append("✓ 无依赖冲突")

        except subprocess.TimeoutExpired:
            self.warnings.append("依赖检查超时")
            score -= 0.1
        except FileNotFoundError:
            # uv 不可用，回退到 pip 检查
            return self._check_dependencies_pip(score)

        return max(0.0, score)

    def _check_dependencies_pip(self, score: float) -> float:
        """使用 pip 检查依赖"""
        pip_path = self._get_pip_path()
        if pip_path.exists():
            try:
                result = subprocess.run(
                    [str(pip_path), "check"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    # 有依赖问题
                    self.warnings.append("发现依赖冲突或不兼容")
                    score -= 0.3

                    # 解析 pip check 输出
                    if "No broken requirements" not in result.stdout:
                        self.suggestions.append(
                            "运行: pip check 查看详细冲突信息"
                        )

                        # 提供解决方案
                        self._analyze_dependency_issues(result.stdout + result.stderr)
                else:
                    self.suggestions.append("✓ 无依赖冲突")

            except subprocess.TimeoutExpired:
                self.warnings.append("依赖检查超时")
                score -= 0.1

        return max(0.0, score)

    def _analyze_dependency_issues(self, output: str) -> None:
        """分析依赖问题并提供解决建议"""
        output_lower = output.lower()

        # 常见问题模式
        patterns = {
            "numpy": "numpy 版本冲突 - 建议使用最新版本",
            "torch": "PyTorch 版本问题 - 访问 https://pytorch.org 获取正确安装命令",
            "tensorflow": "TensorFlow 版本问题 - 确保与 Python 版本兼容",
            "cuda": "CUDA 版本不匹配 - 检查 nvidia-smi 和驱动版本",
            "tensorflow-gpu": "建议使用 tensorflow[and-cuda] 替代 tensorflow-gpu"
        }

        for keyword, suggestion in patterns.items():
            if keyword in output_lower:
                self.suggestions.append(f"💡 {suggestion}")

        # 特殊平台问题
        if "built for a different platform" in output_lower:
            import platform
            machine = platform.machine()
            self.suggestions.append(
                f"💡 平台不匹配 - 运行: uv pip install --force-reinstall torch"
            )
            if machine == "arm64":
                self.suggestions.append(
                    "   Apple Silicon 用户: 确保 PyTorch 安装了 arm64 版本"
                )

    def _check_gpu(self) -> float:
        """检查 GPU/CUDA 状态"""
        score = 1.0

        # 检查 nvidia-smi
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
                 "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )

            if result.returncode == 0:
                gpu_info = result.stdout.strip()
                self.suggestions.append(f"✓ GPU 检测到:\n{gpu_info}")
            else:
                # 检查 Apple Silicon
                import platform
                if platform.machine() == "arm64" and platform.system() == "Darwin":
                    self.suggestions.append("✓ Apple Silicon GPU (MPS) 可用")
                else:
                    self.warnings.append("未检测到 GPU/NVIDIA 驱动")
                    score -= 0.3
        except FileNotFoundError:
            self.warnings.append("nvidia-smi 不可用（无 NVIDIA GPU）")
        except subprocess.TimeoutExpired:
            self.warnings.append("GPU 检测超时")
            score -= 0.1
        except Exception as e:
            self.warnings.append(f"GPU 检测出错: {e}")
            score -= 0.1

        # 检查 PyTorch CUDA
        try:
            import torch
            if torch.cuda.is_available():
                self.suggestions.append(f"✓ PyTorch CUDA: {torch.version.cuda}")
            else:
                self.warnings.append("PyTorch 无法使用 CUDA（可能安装了 CPU 版本）")
                score -= 0.2
        except ImportError:
            pass  # PyTorch 未安装，这是正常的

        return max(0.0, score)

    def _check_compatibility(self) -> float:
        """检查包版本兼容性"""
        score = 1.0

        # 检查 Python 版本
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if sys.version_info < (3, 10):
            self.issues.append(f"Python 版本过低 ({py_version})，需要 3.10+")
            self.suggestions.append("升级 Python 或使用 pyenv 安装 3.10+")
            score -= 0.5
        elif sys.version_info >= (3, 13):
            self.warnings.append(f"Python {py_version} 较新，某些包可能不兼容")

        # 检查常见包版本
        package_checks = self._check_common_packages()
        for status in package_checks.values():
            if status == "incompatible":
                score -= 0.2
            elif status == "warning":
                score -= 0.1

        return max(0.0, score)

    def _check_common_packages(self) -> Dict[str, str]:
        """检查常见包的版本兼容性"""
        results = {}

        # 检查 numpy
        try:
            import numpy
            np_version = numpy.__version__
            # 检查是否是兼容版本
            major, minor = map(int, np_version.split('.')[:2])
            if (major, minor) < (1, 20):
                results["numpy"] = "warning"
                self.suggestions.append(f"NumPy {np_version} 较旧，建议升级到 1.20+")
            else:
                results["numpy"] = "ok"
        except ImportError:
            results["numpy"] = "not_installed"

        # 检查 pandas
        try:
            import pandas
            pd_version = pandas.__version__
            results["pandas"] = "ok"
        except ImportError:
            results["pandas"] = "not_installed"

        # 检查 scikit-learn
        try:
            import sklearn
            skl_version = sklearn.__version__
            results["scikit-learn"] = "ok"
        except ImportError:
            results["scikit-learn"] = "not_installed"

        return results

    def _check_disk(self) -> float:
        """检查磁盘空间"""
        score = 1.0

        try:
            import shutil
            total, used, free = shutil.disk_usage(self.project_path)

            free_gb = free / (1024**3)
            if free_gb < 1:
                self.issues.append(f"磁盘空间不足: 仅剩 {free_gb:.1f}GB")
                score -= 0.3
            elif free_gb < 5:
                self.warnings.append(f"磁盘空间偏低: {free_gb:.1f}GB 可用")
                score -= 0.1
        except Exception:
            pass

        return score

    def _get_pip_path(self) -> Path:
        """获取 pip 路径"""
        pip_path = self.venv_path / "bin" / "pip"
        if sys.platform == "win32":
            pip_path = self.venv_path / "Scripts" / "pip.exe"
        return pip_path

    def print_report(self, results: Dict[str, Any]) -> None:
        """打印健康检查报告"""
        console.print("\n")
        console.print(Panel.fit(
            f"[bold]环境健康检查[/bold]\n"
            f"状态: {self._get_status_emoji(results['status'])} {results['status'].upper()}",
            title="ML Easy Setup"
        ))

        # 打印分数
        console.print("\n[bold]健康分数:[/bold]")
        for name, score in results["scores"].items():
            status_icon = "✓" if score >= 0.8 else "⚠" if score >= 0.5 else "✗"
            bar = self._get_score_bar(score)
            console.print(f"  {status_icon} {name}: {bar}")

        # 打印建议
        if results["issues"] or results["warnings"] or results["suggestions"]:
            console.print("\n[bold]发现的问题:[/bold]")

            for issue in results["issues"]:
                console.print(f"  [red]✗[/red] {issue}")

            for warning in results["warnings"]:
                console.print(f"  [yellow]⚠[/yellow] {warning}")

            if results["suggestions"]:
                console.print("\n[bold]建议:[/bold]")
                for i, suggestion in enumerate(results["suggestions"], 1):
                    console.print(f"  {i}. {suggestion}")

        console.print("")

    def _get_status_emoji(self, status: str) -> str:
        """获取状态 emoji"""
        return {
            "healthy": "[green]✓[/green]",
            "warning": "[yellow]⚠[/yellow]",
            "critical": "[red]✗[/red]"
        }.get(status, "?")

    def _get_score_bar(self, score: float) -> str:
        """生成分数条"""
        filled = int(score * 20)
        color = "green" if score >= 0.8 else "yellow" if score >= 0.5 else "red"

        bar = "█" * filled + "░" * (20 - filled)
        return f"[{color}]{bar}[/{color}] {int(score * 100)}%"

    def auto_fix(self, results: Dict[str, Any], dry_run: bool = True) -> List[str]:
        """
        尝试自动修复问题

        Args:
            results: 健康检查结果
            dry_run: 是否只显示会执行的操作而不实际执行

        Returns:
            执行的操作列表
        """
        actions = []

        # 1. 升级 pip
        if results["scores"]["venv"] < 0.8:
            pip_path = self._get_pip_path()
            if pip_path.exists():
                action = f"升级 pip: {pip_path} install --upgrade pip"
                actions.append(action)
                if not dry_run:
                    subprocess.run(
                        [str(pip_path), "install", "--upgrade", "pip"],
                        check=True
                    )

        # 2. 修复依赖
        if results["scores"]["dependencies"] < 0.8:
            req_file = self.project_path / "requirements.txt"
            if req_file.exists():
                action = "重新安装依赖以解决冲突"
                actions.append(action)
                if not dry_run:
                    pip_path = self._get_pip_path()
                    subprocess.run(
                        [str(pip_path), "install", "-r", str(req_file), "--force-reinstall"],
                        check=True
                    )

        return actions


def check_command(path: str = ".") -> None:
    """
    健康检查命令

    Args:
        path: 项目路径
    """
    project_path = Path(path).resolve()

    if not (project_path / ".venv").exists():
        console.print("[red]错误:[/red] 当前目录不是 ML Easy Setup 项目")
        console.print("请运行: mlsetup create <project-name>")
        return

    checker = HealthChecker(project_path)
    results = checker.check_all()
    checker.print_report(results)

    # 如果有严重问题，询问是否自动修复
    if results["status"] == "critical" and results["issues"]:
        from rich.prompt import Confirm

        if Confirm.ask("\n是否尝试自动修复这些问题？"):
            actions = checker.auto_fix(results, dry_run=False)
            console.print(f"\n[green]✓ 已执行 {len(actions)} 项修复操作[/green]")
