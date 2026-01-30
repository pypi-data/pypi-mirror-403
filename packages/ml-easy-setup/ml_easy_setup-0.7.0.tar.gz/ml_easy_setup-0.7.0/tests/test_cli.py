"""
CLI 测试
"""

import pytest
from click.testing import CliRunner

from ml_easy_setup.cli import main


def test_main_command():
    """测试主命令"""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "ML Easy Setup" in result.output


def test_list_templates():
    """测试列出模板"""
    runner = CliRunner()
    result = runner.invoke(main, ["list-templates"])
    assert result.exit_code == 0
    assert "模板名称" in result.output


def test_detect_command():
    """测试检测命令"""
    runner = CliRunner()
    result = runner.invoke(main, ["detect"])
    assert result.exit_code == 0
