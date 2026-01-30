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
from ml_easy_setup.core.health import check_command
from ml_easy_setup.core.container import ContainerManager, ContainerConfig
from ml_easy_setup.core.distributed import DistributedConfigManager, DistributedConfig

console = Console()


@click.group()
@click.version_option(version="0.4.0", prog_name="ml-easy-setup")
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
    type=click.Choice([
        "minimal", "pytorch", "tensorflow", "nlp", "cv", "rl",
        "model-builder", "algorithm-validator", "data-science",
        "gradient-boosting", "mlops", "timeseries", "graph",
        "llm", "rag", "inference",  # 新增 LLM/GenAI 模板
        "full"
    ]),
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
@click.option(
    "--docker",
    is_flag=True,
    help="生成 Dockerfile 和容器配置"
)
@click.option(
    "--devcontainer",
    is_flag=True,
    help="生成 VS Code DevContainer 配置"
)
@click.option(
    "--pyproject",
    is_flag=True,
    help="使用 pyproject.toml (现代 Python 打包标准)"
)
@click.option(
    "--rocm",
    is_flag=True,
    help="使用 ROCm (AMD GPU 支持)"
)
@click.option(
    "--rocm-version",
    type=click.Choice(["5.4", "5.5", "5.6", "5.7"]),
    default="5.7",
    help="ROCm 版本 (默认: 5.7)"
)
@click.option(
    "--distributed",
    is_flag=True,
    help="生成分布式训练配置 (accelerate/DeepSpeed)"
)
def create(
    name: str,
    template: str,
    cuda: str,
    python: str,
    path: str | None,
    docker: bool,
    devcontainer: bool,
    pyproject: bool,
    rocm: bool,
    rocm_version: str,
    distributed: bool
):
    """
    创建新的 ML 项目环境

    示例:
        mlsetup create my-project --template pytorch --cuda auto
        mlsetup create my-project --template pytorch --docker
        mlsetup create my-project --template nlp --devcontainer
        mlsetup create my-project --template llm --pyproject --cuda 12.1
        mlsetup create my-project --template llm --rocm --distributed
        mlsetup create my-project --template llm --pyproject --cuda 12.1 --distributed
    """
    project_path = Path(path) if path else Path.cwd() / name
    project_path = project_path.resolve()

    # 配置提示
    hints = []
    if docker or devcontainer:
        container_hint = 'Docker' if docker else ''
        container_hint += ' + ' if docker and devcontainer else ''
        container_hint += 'DevContainer' if devcontainer else ''
        hints.append(f"容器: {container_hint}")

    if pyproject:
        hints.append("依赖: pyproject.toml")

    if rocm:
        hints.append(f"ROCm: {rocm_version}")

    if distributed:
        hints.append("分布式: 是")

    hint_str = "\n" + "\n".join(hints) if hints else ""
    compute_str = f"ROCm {rocm_version}" if rocm else f"CUDA {cuda}"

    console.print(Panel.fit(
        f"[bold cyan]创建项目: {name}[/bold cyan]\n"
        f"模板: {template} | {compute_str} | Python: {python}{hint_str}\n"
        f"路径: {project_path}",
        title="ML Easy Setup"
    ))

    try:
        # 检测硬件
        detector = HardwareDetector()

        # GPU 数量检测 (用于分布式配置)
        gpu_count = detector.detect_gpu_count()
        gpu_type = "amd" if rocm else "nvidia"

        # CUDA/ROCm 版本检测
        if rocm:
            # ROCm 模式
            detected_rocm = detector.detect_rocm()
            if detected_rocm:
                console.print(f"🎯 检测到 ROCm 版本: [green]{detected_rocm}[/green]")
                rocm_version = detected_rocm
            cuda = "none"  # ROCm 模式下禁用 CUDA
        elif cuda == "auto":
            # CUDA 自动检测模式
            detected_cuda = detector.detect_cuda()
            if detected_cuda:
                console.print(f"🎯 检测到 CUDA 版本: [green]{detected_cuda}[/green]")
                cuda = detected_cuda
            else:
                # 检测是否有 AMD GPU
                detected_rocm = detector.detect_rocm()
                if detected_rocm:
                    console.print(f"🎯 检测到 AMD GPU，使用 ROCm [green]{detected_rocm}[/green]")
                    rocm = True
                    rocm_version = detected_rocm
                    cuda = "none"
        elif cuda == "cpu":
            cuda = "none"

        # 创建环境
        env_manager = EnvironmentManager(project_path)
        template_manager = TemplateManager()

        console.print("\n[bold]步骤 1/3:[/bold] 创建项目结构...")
        env_manager.create_project_structure(name)

        console.print("[bold]步骤 2/3:[/bold] 加载模板并解析依赖...")
        template_config = template_manager.load_template(
            template,
            cuda,
            use_rocm=rocm,
            rocm_version=rocm_version
        )
        dependencies = template_config.get("dependencies", [])
        dev_dependencies = template_config.get("dev_dependencies", [])

        console.print(f"   需要安装 [cyan]{len(dependencies)}[/cyan] 个核心依赖")
        console.print(f"   需要安装 [cyan]{len(dev_dependencies)}[/cyan] 个开发依赖")

        console.print("\n[bold]步骤 3/4:[/bold] 创建虚拟环境并安装依赖...")
        env_manager.create_environment(python, dependencies, dev_dependencies)

        # 生成项目文件
        console.print("\n[bold]步骤 4/4:[/bold] 生成项目文件...")
        env_manager.generate_project_files(name, template_config, use_pyproject=pyproject)

        # 生成容器配置
        if docker or devcontainer:
            container_manager = ContainerManager(project_path)
            container_config = ContainerConfig(
                project_name=name,
                template_type=template_config.get("type", "minimal"),
                cuda_version=cuda,
                python_version=python,
                dependencies=dependencies,
                include_devcontainer=devcontainer
            )

            if docker:
                console.print("   [dim]生成 Dockerfile...[/dim]")
                container_manager.generate_dockerfile(container_config)
                container_manager.generate_dockerignore()
                container_manager.generate_readme_addon(container_config)

            if devcontainer:
                console.print("   [dim]生成 DevContainer 配置...[/dim]")
                container_manager.generate_devcontainer(container_config)

        # 生成分布式配置
        if distributed:
            num_gpus = gpu_count["total"]
            if num_gpus > 0:
                console.print("\n[bold]步骤 5/5:[/bold] 生成分布式训练配置...")
                console.print(f"   检测到 {num_gpus} 个 {gpu_type.upper()} GPU")

                dist_manager = DistributedConfigManager(project_path)
                dist_config = DistributedConfig(
                    project_path=project_path,
                    num_gpus=num_gpus,
                    gpu_type=gpu_type,
                    template_type=template_config.get("type", "minimal"),
                )

                # 生成 accelerate 配置
                dist_manager.generate_accelerate_config(
                    num_gpus=num_gpus,
                    gpu_type=gpu_type,
                )

                # 生成 DeepSpeed 配置
                dist_manager.generate_deepspeed_config(num_gpus=num_gpus)

                # 生成 FSDP 配置 (PyTorch 模板)
                if template_config.get("type") == "pytorch":
                    dist_manager.generate_fsdp_config(num_gpus=num_gpus)

                # 生成训练脚本
                dist_manager.generate_training_script(
                    template_type=template_config.get("type", "minimal"),
                    num_gpus=num_gpus,
                )

                # 生成启动配置
                dist_manager.generate_launch_config(
                    num_gpus=num_gpus,
                    template_type=template_config.get("type", "minimal"),
                )

                # 生成多 GPU 训练示例
                dist_manager.generate_multi_gpu_example()
            else:
                console.print("\n[yellow]未检测到 GPU，跳过分布式配置[/yellow]")

        console.print("\n" + "=" * 50)
        console.print("[bold green]✓ 环境配置完成！[/bold green]")
        console.print("=" * 50)
        console.print(f"\n下一步操作:")
        console.print(f"  [cyan]cd {name}[/cyan]")
        console.print(f"  [cyan]source .venv/bin/activate[/cyan]  # Linux/Mac")
        console.print(f"  [cyan]\\.venv\\Scripts\\activate[/cyan]  # Windows")
        console.print(f"  [cyan]python -c 'import torch; print(torch.__version__)'[/cyan]")

        # 容器相关提示
        if docker:
            console.print(f"\n[bold]容器化部署:[/bold]")
            console.print(f"  [cyan]docker build -t {name}:latest .[/cyan]")
            console.print(f"  [cyan]docker run -it --rm --gpus all -p 8888:8888 {name}:latest[/cyan]")

        if devcontainer:
            console.print(f"\n[bold]DevContainer:[/bold]")
            console.print(f"  在 VS Code 中按 [cyan]F1[/cyan] → [cyan]Dev Containers: Reopen in Container[/cyan]")

        # 分布式训练相关提示
        if distributed and gpu_count["total"] > 0:
            console.print(f"\n[bold]分布式训练:[/bold]")
            console.print(f"  [cyan]accelerate launch --config_file accelerate_config.yaml src/train.py[/cyan]")
            console.print(f"  [cyan]bash scripts/train_distributed.sh[/cyan]")
            console.print(f"  [cyan]deepspeed --num_gpus={gpu_count['total']} src/train.py --deepspeed ds_config.json[/cyan]")

        # pyproject 相关提示
        if pyproject:
            console.print(f"\n[bold]pyproject.toml:[/bold]")
            console.print(f"  [cyan]uv sync --group dev[/cyan]  # 安装开发依赖")
            console.print(f"  [cyan]uv lock[/cyan]  # 生成锁文件")

        # ROCm 相关提示
        if rocm:
            console.print(f"\n[bold]ROCm (AMD GPU):[/bold]")
            console.print(f"  PyTorch ROCm 版本已配置在 requirements.txt 中")
            console.print(f"  确保系统已安装 ROCm: [cyan]rocm-smi --showversion[/cyan]")

        console.print(f"\n[yellow]更多容器化文档: [cyan]README_CONTAINER.md[/cyan][/yellow]")

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
def llm_check():
    """
    LLM 硬件兼容性检查

    检查 GPU、CUDA、Flash Attention 等与 LLM 训练相关的硬件信息
    """
    from rich.panel import Panel
    from rich.syntax import Syntax

    detector = HardwareDetector()
    report = detector.get_llm_hardware_report()

    console.print("\n[bold cyan]🔍 LLM 硬件兼容性检查[/bold cyan]\n")

    # GPU 信息
    console.print("[bold]GPU 信息:[/bold]")
    if report["gpu_available"]:
        console.print(f"  GPU: [green]{report['gpu_name']}[/green]")
        console.print(f"  Compute Capability: [cyan]{report['compute_capability']}[/cyan]")
    else:
        console.print("  [yellow]未检测到 NVIDIA GPU[/yellow]")

    # CUDA 信息
    console.print(f"\n[bold]CUDA 版本:[/bold]")
    if report["cuda_version"]:
        console.print(f"  [green]{report['cuda_version']}[/green]")
    else:
        console.print("  [yellow]未安装 CUDA[/yellow]")

    # Flash Attention 信息
    console.print(f"\n[bold]Flash Attention:[/bold]")
    if report["flash_attention"]["compatible"]:
        console.print("  [green]✓ 兼容[/green] - " + report["flash_attention"]["reason"])
        if report["flash_attention"]["install_command"]:
            console.print("\n  [dim]安装命令:[/dim]")
            install_cmd = report["flash_attention"]["install_command"]
            for line in install_cmd.split("\n"):
                console.print(f"    {line}")
    else:
        console.print("  [yellow]✗ 不兼容[/yellow] - " + report["flash_attention"]["reason"])

    # 推荐设置
    if report["recommended_settings"]:
        console.print(f"\n[bold]推荐训练设置:[/bold]")
        for key, value in report["recommended_settings"].items():
            value_str = "[green]" + str(value) + "[/green]" if value is True else str(value)
            console.print(f"  {key}: {value_str}")

    console.print()


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


@main.command()
@click.option("--path", "-p", type=click.Path(), default=".", help="项目路径")
@click.option("--auto-fix", is_flag=True, help="自动修复发现的问题")
def health(path: str, auto_fix: bool) -> None:
    """
    环境健康检查

    检查项目环境状态，发现潜在问题并提供修复建议。

    示例:
        mlsetup health
        mlsetup health --auto-fix
    """
    from rich.prompt import Confirm

    project_path = Path(path).resolve()

    # 检查是否是我们的项目（有 .venv 或 requirements.txt）
    has_venv = (project_path / ".venv").exists()
    has_req = (project_path / "requirements.txt").exists()

    if not (has_venv or has_req):
        console.print("[yellow]提示:[/yellow] 当前目录可能不是 ML Easy Setup 项目")
        console.print("尝试运行检查...")
    else:
        console.print("[green]✓[/green] 检测到 ML Easy Setup 项目结构")

    from ml_easy_setup.core.health import HealthChecker

    checker = HealthChecker(project_path)
    results = checker.check_all()
    checker.print_report(results)

    # 询问是否自动修复
    if results["status"] in ["warning", "critical"]:
        if auto_fix or Confirm.ask("\n是否尝试自动修复这些问题？"):
            actions = checker.auto_fix(results, dry_run=not auto_fix)

            if not auto_fix:
                console.print("\n[bold]将执行以下操作:[/bold]")
                for i, action in enumerate(actions, 1):
                    console.print(f"  {i}. {action}")

                if Confirm.ask("\n是否继续？"):
                    actions = checker.auto_fix(results, dry_run=False)
                    console.print(f"\n[green]✓ 已执行 {len(actions)} 项修复操作[/green]")


if __name__ == "__main__":
    main()
