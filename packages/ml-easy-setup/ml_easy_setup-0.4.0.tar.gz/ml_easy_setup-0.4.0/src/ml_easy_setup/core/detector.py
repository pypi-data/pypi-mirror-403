"""
硬件检测器 - 检测系统硬件和软件环境
"""

import subprocess
import sys
import platform
from typing import Dict, Any


class HardwareDetector:
    """硬件检测器"""

    def __init__(self):
        self.system_info = self._get_system_info()

    def detect_all(self, verbose: bool = False) -> Dict[str, Any]:
        """
        检测所有系统信息

        Args:
            verbose: 是否显示详细信息

        Returns:
            包含所有检测信息的字典
        """
        info = {
            "操作系统": self.system_info["os"],
            "Python 版本": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "架构": self.system_info["machine"],
        }

        # CUDA 检测
        cuda_info = self.detect_cuda()
        info["CUDA"] = cuda_info if cuda_info else "未安装"

        # GPU 检测
        gpu_info = self.detect_gpu()
        if gpu_info:
            info["GPU"] = gpu_info

        # UV 检测
        uv_version = self._check_uv()
        info["UV"] = uv_version if uv_version else "未安装"

        if verbose:
            info["详细系统信息"] = self._get_detailed_system_info()

        return info

    def detect_cuda(self) -> str | None:
        """
        检测 CUDA 版本

        Returns:
            CUDA 版本字符串，如果未安装返回 None
        """
        try:
            result = subprocess.run(
                ["nvcc", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # 解析 nvcc 输出
                for line in result.stdout.split("\n"):
                    if "release" in line.lower():
                        # 提取版本号
                        import re
                        match = re.search(r"(\d+\.\d+)", line)
                        if match:
                            return match.group(1)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # 尝试通过 nvidia-smi 检测
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # nvidia-smi 存在，但需要从输出中解析 CUDA 版本
                for line in result.stdout.split("\n"):
                    if "CUDA Version" in line:
                        import re
                        match = re.search(r"CUDA Version:\s*(\d+\.\d+)", line)
                        if match:
                            return match.group(1)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    def detect_gpu(self) -> str | None:
        """
        检测 GPU 信息

        Returns:
            GPU 信息字符串，如果未检测到返回 None
        """
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                gpu_names = result.stdout.strip().split("\n")
                if gpu_names and gpu_names[0]:
                    if len(gpu_names) == 1:
                        return gpu_names[0]
                    else:
                        return f"{gpu_names[0]} (+{len(gpu_names)-1} more)"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Apple Silicon GPU
        if self.system_info["machine"] == "arm64" and self.system_info["os"] == "Darwin":
            return "Apple Silicon (MPS)"

        return None

    def _check_uv(self) -> str | None:
        """检查 uv 是否安装"""
        try:
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    def _get_system_info(self) -> Dict[str, str]:
        """获取基础系统信息"""
        return {
            "os": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

    def _get_detailed_system_info(self) -> str:
        """获取详细系统信息"""
        return (
            f"System: {platform.system()}\n"
            f"Node: {platform.node()}\n"
            f"Release: {platform.release()}\n"
            f"Version: {platform.version()}\n"
            f"Machine: {platform.machine()}\n"
            f"Processor: {platform.processor()}\n"
            f"Python: {sys.version}\n"
        )

    def check_package_installed(self, package_name: str) -> bool:
        """
        检查包是否已安装

        Args:
            package_name: 包名

        Returns:
            是否已安装
        """
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False

    def get_package_version(self, package_name: str) -> str | None:
        """
        获取已安装包的版本

        Args:
            package_name: 包名

        Returns:
            版本字符串，如果未安装返回 None
        """
        try:
            module = __import__(package_name)
            return getattr(module, "__version__", "unknown")
        except ImportError:
            return None
