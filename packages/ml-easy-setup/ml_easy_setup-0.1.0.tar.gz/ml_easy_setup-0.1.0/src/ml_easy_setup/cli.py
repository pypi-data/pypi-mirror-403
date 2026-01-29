"""
ML Easy Setup CLI - 命令行接口
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ml_easy_setup.core.env_manager import EnvironmentManager
from ml_easy_setup.core.template import TemplateManager
from ml_easy_setup.core.detector import HardwareDetector

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="ml-easy-setup")
def main():
    """
    ML Easy Setup - 一键配置机器学习/深度学习环境

    让科研工作更专注于算法本身，而不是环境配置。
    """
    pass


@main.command()
@click.argument("name", type=str)
@click.option(
    "--template", "-t",
    type=click.Choice(["pytorch", "tensorflow", "nlp", "cv", "rl", "minimal"]),
    default="minimal",
    help="预配置环境模板"
)
@click.option(
    "--cuda", "-c",
    type=click.Choice(["none", "cpu", "auto", "11.8", "12.1", "12.4"]),
    default="auto",
    help="CUDA 版本 (auto 自动检测)"
)
@click.option(
    "--python", "-p",
    type=str,
    default="3.10",
    help="Python 版本"
)
@click.option(
    "--path", "-d",
    type=click.Path(),
    default=None,
    help="项目路径（默认当前目录）"
)
def create(name: str, template: str, cuda: str, python: str, path: str | None):
    """
    创建新的 ML 项目环境

    示例:
        mlsetup create my-project --template pytorch --cuda auto
    """
    project_path = Path(path) if path else Path.cwd() / name
    project_path = project_path.resolve()

    console.print(Panel.fit(
        f"[bold cyan]创建项目: {name}[/bold cyan]\n"
        f"模板: {template} | CUDA: {cuda} | Python: {python}\n"
        f"路径: {project_path}",
        title="ML Easy Setup"
    ))

    try:
        # 检测硬件
        detector = HardwareDetector()
        if cuda == "auto":
            detected_cuda = detector.detect_cuda()
            console.print(f"🎯 检测到 CUDA 版本: [green]{detected_cuda}[/green]")
            cuda = detected_cuda
        elif cuda == "cpu":
            cuda = "none"

        # 创建环境
        env_manager = EnvironmentManager(project_path)
        template_manager = TemplateManager()

        console.print("\n[bold]步骤 1/3:[/bold] 创建项目结构...")
        env_manager.create_project_structure(name)

        console.print("[bold]步骤 2/3:[/bold] 加载模板并解析依赖...")
        template_config = template_manager.load_template(template, cuda)
        dependencies = template_config.get("dependencies", [])
        dev_dependencies = template_config.get("dev_dependencies", [])

        console.print(f"   需要安装 [cyan]{len(dependencies)}[/cyan] 个核心依赖")
        console.print(f"   需要安装 [cyan]{len(dev_dependencies)}[/cyan] 个开发依赖")

        console.print("\n[bold]步骤 3/3:[/bold] 创建虚拟环境并安装依赖...")
        env_manager.create_environment(python, dependencies, dev_dependencies)

        # 生成项目文件
        env_manager.generate_project_files(name, template_config)

        console.print("\n" + "=" * 50)
        console.print("[bold green]✓ 环境配置完成！[/bold green]")
        console.print("=" * 50)
        console.print(f"\n下一步操作:")
        console.print(f"  [cyan]cd {name}[/cyan]")
        console.print(f"  [cyan]source .venv/bin/activate[/cyan]  # Linux/Mac")
        console.print(f"  [cyan]\\.venv\\Scripts\\activate[/cyan]  # Windows")
        console.print(f"  [cyan]python -c 'import torch; print(torch.__version__)'[/cyan]")

    except Exception as e:
        console.print(f"\n[bold red]✗ 创建失败:[/bold red] {e}")
        raise click.ClickException(str(e))


@main.command()
def list_templates():
    """列出所有可用的环境模板"""
    template_manager = TemplateManager()
    templates = template_manager.list_templates()

    table = Table(title="可用的环境模板")
    table.add_column("模板名称", style="cyan")
    table.add_column("描述", style="white")
    table.add_column("核心库", style="yellow")

    for template in templates:
        table.add_row(
            template["name"],
            template["description"],
            ", ".join(template["core_packages"][:3]) + ("..." if len(template["core_packages"]) > 3 else "")
        )

    console.print(table)


@main.command()
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def detect(verbose: bool):
    """检测系统硬件和软件环境"""
    detector = HardwareDetector()
    info = detector.detect_all(verbose)

    table = Table(title="系统环境检测")
    table.add_column("项目", style="cyan")
    table.add_column("检测结果", style="green")

    for key, value in info.items():
        table.add_row(key, str(value))

    console.print(table)


@main.command()
@click.argument("packages", nargs=-1, required=True)
@click.option("--dev", is_flag=True, help="安装到开发依赖")
def add(packages: tuple[str, ...], dev: bool):
    """
    添加额外的包到当前项目

    示例:
        mlsetup add numpy pandas
        mlsetup add pytest --dev
    """
    env_manager = EnvironmentManager(Path.cwd())

    console.print(f"[bold]添加包:[/bold] {', '.join(packages)}")

    try:
        env_manager.add_packages(list(packages), dev=dev)
        console.print("[bold green]✓ 包安装完成[/bold green]")
    except Exception as e:
        console.print(f"[bold red]✗ 安装失败:[/bold red] {e}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
