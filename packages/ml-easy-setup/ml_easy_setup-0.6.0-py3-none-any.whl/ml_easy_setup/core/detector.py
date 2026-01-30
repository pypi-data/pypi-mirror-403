"""
硬件检测器 - 检测系统硬件和软件环境
"""

import subprocess
import sys
import platform
import re
from typing import Dict, Any, Optional, Tuple


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
        # 首先检测 NVIDIA GPU
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

        # 检测 AMD GPU (ROCm)
        try:
            result = subprocess.run(
                ["rocm-smi", "--showproductname", "--csv"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # 解析 ROCm 输出获取 GPU 名称
                lines = result.stdout.split("\n")
                for line in lines:
                    if "Card Series" in line or "GPU" in line:
                        # 提取 GPU 名称
                        parts = line.split(",")
                        for part in parts:
                            if "Series" in part or "RX" in part or "MI" in part:
                                gpu_name = part.strip().strip('"')
                                return f"AMD {gpu_name} (ROCm)"
                return "AMD GPU (ROCm)"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Apple Silicon GPU
        if self.system_info["machine"] == "arm64" and self.system_info["os"] == "Darwin":
            return "Apple Silicon (MPS)"

        return None

    def detect_rocm(self) -> str | None:
        """
        检测 ROCm 版本

        Returns:
            ROCm 版本字符串，如果未安装返回 None
        """
        try:
            result = subprocess.run(
                ["rocm-smi", "--showversion", "--csv"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # 解析 ROCm 版本
                for line in result.stdout.split("\n"):
                    if "version" in line.lower():
                        import re
                        match = re.search(r"(\d+\.\d+(\.\d+)?)", line)
                        if match:
                            return match.group(1)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    def detect_gpu_count(self) -> Dict[str, int]:
        """
        检测 GPU 数量

        Returns:
            字典，包含各类型 GPU 的数量
        """
        gpu_count = {
            "nvidia": 0,
            "amd": 0,
            "total": 0,
        }

        # NVIDIA GPU 数量
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=count", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                gpu_count["nvidia"] = int(result.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass

        # AMD GPU 数量
        try:
            result = subprocess.run(
                ["rocm-smi", "--showcount", "--csv"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # 解析 AMD GPU 数量
                match = re.search(r"(\d+)", result.stdout)
                if match:
                    gpu_count["amd"] = int(match.group(1))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        gpu_count["total"] = gpu_count["nvidia"] + gpu_count["amd"]

        return gpu_count

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

    def get_gpu_compute_capability(self) -> Optional[Tuple[str, float]]:
        """
        获取 GPU 计算能力

        Returns:
            元组 (GPU名称, 计算能力版本)，如果检测失败返回 None
        """
        try:
            # 获取 GPU 名称和计算能力
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,compute_cap", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines and lines[0]:
                    # 解析 "NVIDIA GeForce RTX 3090, 8.6" 格式
                    parts = lines[0].split(",")
                    if len(parts) >= 2:
                        gpu_name = parts[0].strip()
                        compute_cap = float(parts[1].strip())
                        return gpu_name, compute_cap
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass

        return None

    def check_flash_attention_compatibility(self) -> Dict[str, Any]:
        """
        检查 Flash Attention 兼容性

        Returns:
            包含兼容性信息的字典:
            - supported: 是否支持
            - reason: 原因说明
            - gpu_info: GPU 信息
            - install_command: 推荐的安装命令
        """
        result = {
            "supported": False,
            "reason": "",
            "gpu_info": None,
            "install_command": None,
        }

        # 首先检查是否有 NVIDIA GPU
        gpu_info = self.get_gpu_compute_capability()

        if gpu_info is None:
            result["reason"] = "未检测到 NVIDIA GPU，Flash Attention 仅支持 NVIDIA GPU"
            return result

        gpu_name, compute_cap = gpu_info
        result["gpu_info"] = {"name": gpu_name, "compute_capability": compute_cap}

        # Flash Attention 2.x 需要 Compute Capability >= 8.0 (Ampere 及更新架构)
        if compute_cap >= 8.0:
            result["supported"] = True
            result["reason"] = f"GPU {gpu_name} (Compute Capability {compute_cap}) 支持 Flash Attention"

            # 根据 CUDA 版本推荐安装命令
            cuda_version = self.detect_cuda()
            if cuda_version:
                result["install_command"] = (
                    f"pip install flash-attn --no-build-isolation\n"
                    f"# 或使用预编译 wheel (更快):\n"
                    f"# pip install flash-attn==2.5.8 --find-links "
                    f"https://github.com/Dao-AILab/flash-attention/releases"
                )
            else:
                result["install_command"] = (
                    "pip install flash-attn --no-build-isolation\n"
                    "# 注意: 需要先安装 CUDA toolkit"
                )
        else:
            architectures = {
                7.5: "Turing (RTX 20 系列, Tesla T4)",
                7.0: "Volta (V100, Titan V)",
                6.1: "Pascal (GTX 10 系列, Titan Xp)",
            }
            arch_name = architectures.get(compute_cap, f"Compute Capability {compute_cap}")

            result["reason"] = (
                f"GPU {gpu_name} 架构 ({arch_name}) 不支持 Flash Attention。\n"
                f"Flash Attention 需要 Ampere (Compute Capability >= 8.0) 或更新架构。\n"
                f"建议使用 xFormers 作为替代: pip install xformers"
            )
            result["install_command"] = "pip install xformers"

        return result

    def detect_flash_attention_installed(self) -> Optional[str]:
        """
        检测 Flash Attention 是否已安装

        Returns:
            版本字符串，如果未安装返回 None
        """
        try:
            import flash_attn
            return getattr(flash_attn, "__version__", "installed (unknown version)")
        except ImportError:
            return None

    def get_llm_hardware_report(self) -> Dict[str, Any]:
        """
        获取 LLM 训练相关的完整硬件报告

        Returns:
            包含 GPU、CUDA、Flash Attention 等信息的字典
        """
        report = {
            "gpu_available": False,
            "gpu_name": None,
            "cuda_version": None,
            "flash_attention": {
                "installed": False,
                "version": None,
                "compatible": False,
                "reason": None,
            },
            "recommended_settings": {},
        }

        # GPU 信息
        gpu_info = self.get_gpu_compute_capability()
        if gpu_info:
            report["gpu_available"] = True
            report["gpu_name"] = gpu_info[0]
            report["compute_capability"] = gpu_info[1]

        # CUDA 版本
        cuda_version = self.detect_cuda()
        if cuda_version:
            report["cuda_version"] = cuda_version

        # Flash Attention 检查
        flash_attn_version = self.detect_flash_attention_installed()
        if flash_attn_version:
            report["flash_attention"]["installed"] = True
            report["flash_attention"]["version"] = flash_attn_version

        flash_attn_compat = self.check_flash_attention_compatibility()
        report["flash_attention"]["compatible"] = flash_attn_compat["supported"]
        report["flash_attention"]["reason"] = flash_attn_compat["reason"]
        report["flash_attention"]["install_command"] = flash_attn_compat.get("install_command")

        # 推荐设置
        if report["gpu_available"]:
            cc = report["compute_capability"]
            if cc >= 8.0:
                report["recommended_settings"] = {
                    "use_flash_attention": True,
                    "use_bitsandbytes": True,
                    "use_deepspeed": True,
                    "max_batch_size": "auto",
                    "gradient_checkpointing": True,
                }
            elif cc >= 7.0:
                report["recommended_settings"] = {
                    "use_flash_attention": False,
                    "use_xformers": True,
                    "use_bitsandbytes": True,
                    "gradient_checkpointing": True,
                }
            else:
                report["recommended_settings"] = {
                    "use_flash_attention": False,
                    "use_bitsandbytes": True,
                    "gradient_checkpointing": True,
                    "use_cpu_offload": True,
                }

        return report
