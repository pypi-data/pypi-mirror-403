"""
ML Easy Setup - 一键配置机器学习/深度学习环境

解决依赖冲突和配置难题，让科研工作更专注于算法本身。
"""

__version__ = "0.4.0"

from ml_easy_setup.core.env_manager import EnvironmentManager
from ml_easy_setup.core.template import TemplateManager

__all__ = ["EnvironmentManager", "TemplateManager", "__version__"]
