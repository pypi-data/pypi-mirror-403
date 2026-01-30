"""
模板管理器测试
"""

import pytest

from ml_easy_setup.core.template import TemplateManager, BUILTIN_TEMPLATES


def test_template_manager_init():
    """测试模板管理器初始化"""
    manager = TemplateManager()
    assert manager is not None


def test_load_builtin_template():
    """测试加载内置模板"""
    manager = TemplateManager()
    config = manager.load_template("minimal")
    assert config["type"] == "minimal"
    assert "dependencies" in config
    assert len(config["dependencies"]) > 0


def test_load_pytorch_template():
    """测试加载 PyTorch 模板"""
    manager = TemplateManager()
    config = manager.load_template("pytorch")
    assert config["type"] == "pytorch"
    assert any("torch" in dep for dep in config["dependencies"])


def test_list_templates():
    """测试列出所有模板"""
    manager = TemplateManager()
    templates = manager.list_templates()
    assert len(templates) > 0
    assert any(t["name"] == "pytorch" for t in templates)
    assert any(t["name"] == "tensorflow" for t in templates)
