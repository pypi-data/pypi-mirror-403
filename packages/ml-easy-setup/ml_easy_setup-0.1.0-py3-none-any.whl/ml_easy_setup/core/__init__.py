"""
核心功能模块
"""

from ml_easy_setup.core.env_manager import EnvironmentManager
from ml_easy_setup.core.template import TemplateManager
from ml_easy_setup.core.detector import HardwareDetector
from ml_easy_setup.core.resolver import DependencyResolver

__all__ = [
    "EnvironmentManager",
    "TemplateManager",
    "HardwareDetector",
    "DependencyResolver",
]
