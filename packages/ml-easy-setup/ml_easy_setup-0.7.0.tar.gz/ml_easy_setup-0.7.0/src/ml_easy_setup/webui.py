"""
ML Easy Setup - Web UI (Streamlit)
图形化配置界面
"""

import json
from pathlib import Path
from typing import Dict, Any

import streamlit as st

from ml_easy_setup.core.detector import HardwareDetector
from ml_easy_setup.core.template import TemplateManager
from ml_easy_setup.core.env_manager import EnvironmentManager
from ml_easy_setup.core.container import ContainerManager, ContainerConfig
from ml_easy_setup.core.distributed import DistributedConfigManager, DistributedConfig


# ============================================
# 页面配置
# ============================================
st.set_page_config(
    page_title="ML Easy Setup",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .feature-card {
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin: 0.5rem 0;
        background: #f8f9fa;
    }
    .template-selected {
        border: 2px solid #667eea;
        background: #e8eaf6;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# 初始化 Session State
# ============================================
def init_session_state():
    """初始化会话状态"""
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'config' not in st.session_state:
        st.session_state.config = {}
    if 'created' not in st.session_state:
        st.session_state.created = False


init_session_state()


# ============================================
# 硬件检测
# ============================================
@st.cache_data
def detect_hardware() -> Dict[str, Any]:
    """缓存硬件检测结果"""
    detector = HardwareDetector()
    return {
        "system": detector.detect_all(verbose=False),
        "gpu_count": detector.detect_gpu_count(),
        "llm_report": detector.get_llm_hardware_report(),
    }


@st.cache_data
def get_templates() -> Dict[str, Any]:
    """获取所有模板"""
    manager = TemplateManager()
    return {
        "templates": manager.list_templates(),
        "details": {t["name"]: manager.load_template(t["name"], "none")
                   for t in manager.list_templates()}
    }


# ============================================
# UI 组件
# ============================================
def render_header():
    """渲染页面标题"""
    st.markdown("""
    <div class="main-header">
        <h1>🚀 ML Easy Setup</h1>
        <p>一键配置机器学习/深度学习环境 - 无需命令行</p>
    </div>
    """, unsafe_allow_html=True)


def render_step_indicator():
    """渲染步骤指示器"""
    steps = ["📋 基本信息", "🎯 模板选择", "⚙️ 计算配置", "🔧 高级选项", "✅ 创建项目"]
    cols = st.columns(len(steps))

    for i, (col, step) in enumerate(zip(cols, steps), 1):
        if i == st.session_state.step:
            col.markdown(f"<b style='color:#667eea'>{step}</b>", unsafe_allow_html=True)
        elif i < st.session_state.step:
            col.markdown(f"<span style='color:#4caf50'>✓ {step}</span>", unsafe_allow_html=True)
        else:
            col.markdown(f"<span style='color:#9e9e9e'>{step}</span>", unsafe_allow_html=True)


def render_step1_basic_info():
    """步骤1: 基本信息"""
    st.subheader("📋 项目基本信息")

    col1, col2 = st.columns(2)

    with col1:
        project_name = st.text_input(
            "项目名称 *",
            placeholder="my-ml-project",
            help="项目文件夹名称（只能包含字母、数字、连字符）"
        )

    with col2:
        project_path = st.text_input(
            "项目路径",
            value=str(Path.home() / "ml-projects"),
            help="项目将创建在此目录下"
        )

    path_obj = Path(project_path) / project_name if project_name else Path(project_path)

    st.info(f"📁 项目将创建在: `{path_obj}`")

    return {
        "name": project_name,
        "path": str(path_obj),
    }


def render_step2_template_selection(templates_data: Dict):
    """步骤2: 模板选择"""
    st.subheader("🎯 选择项目模板")

    # 模板分类
    categories = {
        "🤖 LLM & GenAI": ["llm", "rag", "inference"],
        "🧠 深度学习": ["pytorch", "tensorflow", "nlp", "cv", "rl"],
        "🔧 高级功能": ["model-builder", "mlops", "algorithm-validator"],
        "📊 数据科学": ["data-science", "timeseries", "graph", "gradient-boosting"],
        "📦 其他": ["minimal", "full"],
    }

    selected_template = None

    for category, template_names in categories.items():
        with st.expander(category, expanded=(category == "🤖 LLM & GenAI")):
            cols = st.columns(min(3, len(template_names)))

            for i, tmpl_name in enumerate(template_names):
                col = cols[i % len(cols)]
                tmpl_info = next(t for t in templates_data["templates"] if t["name"] == tmpl_name)

                with col:
                    if st.button(
                        f"**{tmpl_info['name']}**\n\n{tmpl_info['description'][:50]}...",
                        key=f"tmpl_{tmpl_name}",
                        use_container_width=True,
                    ):
                        selected_template = tmpl_name
                        st.session_state.config["template"] = tmpl_name

    # 显示已选择的模板
    if "template" in st.session_state.config:
        tmpl = st.session_state.config["template"]
        tmpl_detail = templates_data["details"][tmpl]

        st.success(f"✅ 已选择: **{tmpl}**")

        with st.expander("📦 查看依赖详情", expanded=False):
            st.markdown(f"**核心包**: {', '.join(tmpl_detail['core_packages'])}")
            st.markdown(f"**依赖数量**: {len(tmpl_detail['dependencies'])} 个")
            if st.button("显示完整依赖列表", key="show_deps"):
                st.code("\n".join(tmpl_detail['dependencies']), language="text")

    return st.session_state.config.get("template")


def render_step3_compute_config(hardware_info: Dict):
    """步骤3: 计算配置"""
    st.subheader("⚙️ 计算环境配置")

    # 显示硬件检测结果
    with st.expander("🔍 硬件检测结果", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("操作系统", hardware_info["system"].get("操作系统", "Unknown"))

        with col2:
            gpu_count = hardware_info["gpu_count"]["total"]
            st.metric("GPU 数量", f"{gpu_count} 卡")

        with col3:
            cuda_version = hardware_info["system"].get("CUDA", "未安装")
            st.metric("CUDA 版本", cuda_version)

        if gpu_count > 0:
            gpu_type = "NVIDIA" if hardware_info["gpu_count"]["nvidia"] > 0 else "AMD"
            st.info(f"🎮 检测到 {gpu_type} GPU")

    # GPU 类型选择
    gpu_type = st.radio(
        "GPU 类型",
        ["自动检测", "NVIDIA CUDA", "AMD ROCm", "CPU only"],
        horizontal=True,
        help="选择计算后端"
    )

    compute_config = {}

    if gpu_type in ["自动检测", "NVIDIA CUDA"]:
        # 检测 CUDA 版本
        detected_cuda = hardware_info["system"].get("CUDA")
        cuda_options = ["自动"] + (["11.8", "12.1", "12.4"] if detected_cuda else [])

        cuda_version = st.selectbox(
            "CUDA 版本",
            cuda_options,
            index=0,
            help="PyTorch 将根据此版本安装"
        )
        compute_config["cuda"] = cuda_version if cuda_version != "自动" else "auto"
        compute_config["rocm"] = False

    elif gpu_type == "AMD ROCm":
        rocm_version = st.selectbox(
            "ROCm 版本",
            ["5.7", "5.6", "5.5", "5.4"],
            index=0,
            help="AMD GPU 驱动版本"
        )
        compute_config["rocm"] = True
        compute_config["rocm_version"] = rocm_version
        compute_config["cuda"] = "none"

    else:  # CPU only
        compute_config["cuda"] = "none"
        compute_config["rocm"] = False

    # Python 版本
    python_version = st.selectbox(
        "Python 版本",
        ["3.10", "3.11", "3.12"],
        index=0,
        help="建议使用 3.10 以获得最佳兼容性"
    )
    compute_config["python"] = python_version

    return compute_config


def render_step4_advanced_options(hardware_info: Dict):
    """步骤4: 高级选项"""
    st.subheader("🔧 高级功能")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🐳 容器化")
        docker = st.checkbox("生成 Dockerfile", help="生成多阶段 Docker 构建文件")
        devcontainer = st.checkbox(
            "生成 DevContainer 配置",
            help="VS Code 远程开发环境配置"
        )

        st.markdown("#### 📦 依赖管理")
        pyproject = st.checkbox(
            "使用 pyproject.toml",
            value=True,
            help="现代 Python 打包标准，支持 UV dependency groups"
        )

    with col2:
        st.markdown("#### 🚀 分布式训练")
        gpu_count = hardware_info["gpu_count"]["total"]

        if gpu_count > 0:
            distributed = st.checkbox(
                "生成分分布式训练配置",
                value=(gpu_count >= 2),
                help=f"检测到 {gpu_count} 个 GPU，自动生成 Accelerate/DeepSpeed 配置"
            )

            if distributed:
                st.info(f"将生成适合 {gpu_count} GPU 的配置")
        else:
            distributed = False
            st.warning("⚠️ 未检测到 GPU，分布式配置不可用")

        st.markdown("#### 🔍 LLM 优化")
        if gpu_count > 0:
            llm_report = hardware_info["llm_report"]
            if llm_report.get("flash_attention", {}).get("compatible"):
                st.success("✅ 支持 Flash Attention 2.x")
            else:
                st.warning("⚠️ GPU 不支持 Flash Attention")

    return {
        "docker": docker,
        "devcontainer": devcontainer,
        "pyproject": pyproject,
        "distributed": distributed,
    }


def render_step5_create_project():
    """步骤5: 创建项目"""
    st.subheader("✅ 准备创建")

    # 显示配置摘要
    config = st.session_state.config

    st.markdown("### 📋 配置摘要")

    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:
        st.markdown("**基本信息**")
        st.markdown(f"- 项目名称: `{config['name']}`")
        st.markdown(f"- 模板: `{config['template']}`")
        st.markdown(f"- Python: `{config['compute']['python']}`")

    with summary_col2:
        st.markdown("**计算配置**")
        if config['compute'].get('rocm'):
            st.markdown(f"- GPU: AMD ROCm {config['compute']['rocm_version']}")
        elif config['compute']['cuda'] != 'none':
            st.markdown(f"- GPU: CUDA {config['compute']['cuda']}")
        else:
            st.markdown("- GPU: CPU only")

        st.markdown("**高级功能**")
        features = []
        if config['options']['docker']:
            features.append("Docker")
        if config['options']['devcontainer']:
            features.append("DevContainer")
        if config['options']['pyproject']:
            features.append("pyproject.toml")
        if config['options']['distributed']:
            features.append("分布式")
        st.markdown(f"- {', '.join(features) if features else '无'}")

    st.markdown("---")

    # 创建按钮
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🚀 开始创建项目", type="primary", use_container_width=True):
            create_project()


def create_project():
    """执行项目创建"""
    config = st.session_state.config

    # 显示进度
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # 步骤 1: 初始化
        status_text.text("初始化环境...")
        progress_bar.progress(10)

        project_path = Path(config["path"])
        env_manager = EnvironmentManager(project_path)
        template_manager = TemplateManager()
        detector = HardwareDetector()

        # 步骤 2: 创建项目结构
        status_text.text("创建项目结构...")
        env_manager.create_project_structure(config["name"])
        progress_bar.progress(30)

        # 步骤 3: 加载模板
        status_text.text("加载模板并解析依赖...")
        compute_cfg = config["compute"]

        template_config = template_manager.load_template(
            config["template"],
            compute_cfg.get("cuda", "none"),
            use_rocm=compute_cfg.get("rocm", False),
            rocm_version=compute_cfg.get("rocm_version", "5.7")
        )
        progress_bar.progress(50)

        # 步骤 4: 创建虚拟环境
        status_text.text("创建虚拟环境并安装依赖...")
        dependencies = template_config.get("dependencies", [])
        dev_dependencies = template_config.get("dev_dependencies", [])
        env_manager.create_environment(compute_cfg["python"], dependencies, dev_dependencies)
        progress_bar.progress(70)

        # 步骤 5: 生成项目文件
        status_text.text("生成项目文件...")
        env_manager.generate_project_files(
            config["name"],
            template_config,
            use_pyproject=config["options"]["pyproject"]
        )
        progress_bar.progress(80)

        # 步骤 6: 容器配置
        options = config["options"]
        if options["docker"] or options["devcontainer"]:
            status_text.text("生成容器配置...")
            container_manager = ContainerManager(project_path)
            container_config = ContainerConfig(
                project_name=config["name"],
                template_type=template_config.get("type", "minimal"),
                cuda_version=compute_cfg.get("cuda", "none"),
                python_version=compute_cfg["python"],
                dependencies=dependencies,
                include_devcontainer=options["devcontainer"]
            )

            if options["docker"]:
                container_manager.generate_dockerfile(container_config)
                container_manager.generate_dockerignore()
                container_manager.generate_readme_addon(container_config)

            if options["devcontainer"]:
                container_manager.generate_devcontainer(container_config)

        # 步骤 7: 分布式配置
        if options["distributed"]:
            gpu_count = detector.detect_gpu_count()["total"]
            if gpu_count > 0:
                status_text.text("生成分分布式训练配置...")
                dist_manager = DistributedConfigManager(project_path)
                dist_config = DistributedConfig(
                    project_path=project_path,
                    num_gpus=gpu_count,
                    gpu_type="amd" if compute_cfg.get("rocm") else "nvidia",
                    template_type=template_config.get("type", "minimal"),
                )

                dist_manager.generate_accelerate_config(gpu_count, "nvidia")
                dist_manager.generate_deepspeed_config(gpu_count)
                dist_manager.generate_training_script(
                    template_type=template_config.get("type", "minimal"),
                    num_gpus=gpu_count,
                )
                dist_manager.generate_launch_config(gpu_count, template_config.get("type", "minimal"))
                dist_manager.generate_multi_gpu_example()

        progress_bar.progress(100)
        status_text.text("")

        # 成功消息
        st.session_state.created = True

        st.success("""
        ## 🎉 项目创建成功！

        项目已成功创建在指定路径。
        """)

        # 下一步操作
        st.markdown("### 📌 下一步操作")

        st.code(f"""
# 进入项目目录
cd {config['path']}

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\\Scripts\\activate   # Windows

# 验证安装
python -c 'import torch; print(torch.__version__)'
        """, language="bash")

        # 容器操作提示
        if options["docker"]:
            st.markdown("#### 🐳 Docker 构建")
            st.code(f"""
# 构建镜像
docker build -t {config['name']}:latest .

# 运行容器
docker run -it --rm --gpus all -p 8888:8888 {config['name']}:latest
            """, language="bash")

        # 分布式训练提示
        if options["distributed"]:
            st.markdown("#### 🚀 分布式训练")
            st.code("""
# 使用 Accelerate
accelerate launch --config_file accelerate_config.yaml src/train.py

# 使用 DeepSpeed
deepspeed --num_gpus=all src/train.py --deepspeed ds_config.json
            """, language="bash")

        # 重置按钮
        if st.button("创建新项目"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_session_state()
            st.rerun()

    except Exception as e:
        st.error(f"""
        ## ❌ 创建失败

        **错误信息**: {str(e)}

        请检查：
        1. 项目路径是否有写入权限
        2. 网络连接是否正常
        3. Python 环境是否正确
        """)
        st.exception(e)


# ============================================
# 主流程
# ============================================
def main():
    """主界面"""
    render_header()
    render_step_indicator()

    st.markdown("---")

    # 缓存数据
    hardware_info = detect_hardware()
    templates_data = get_templates()

    # 步骤导航
    if st.session_state.step == 1:
        basic_info = render_step1_basic_info()

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("下一步 →", use_container_width=True):
                if basic_info["name"]:
                    st.session_state.config.update(basic_info)
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.warning("请输入项目名称")

    elif st.session_state.step == 2:
        template = render_step2_template_selection(templates_data)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← 上一步", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
        with col2:
            if st.button("下一步 →", use_container_width=True, disabled=(not template)):
                st.session_state.step = 3
                st.rerun()

    elif st.session_state.step == 3:
        compute_config = render_step3_compute_config(hardware_info)
        st.session_state.config["compute"] = compute_config

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← 上一步", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        with col2:
            if st.button("下一步 →", use_container_width=True):
                st.session_state.step = 4
                st.rerun()

    elif st.session_state.step == 4:
        options = render_step4_advanced_options(hardware_info)
        st.session_state.config["options"] = options

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← 上一步", use_container_width=True):
                st.session_state.step = 3
                st.rerun()
        with col2:
            if st.button("下一步 →", use_container_width=True):
                st.session_state.step = 5
                st.rerun()

    elif st.session_state.step == 5:
        render_step5_create_project()

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← 上一步", use_container_width=True):
                st.session_state.step = 4
                st.rerun()

    # 侧边栏：帮助信息
    with st.sidebar:
        st.markdown("## 📖 使用指南")

        st.markdown("""
        ### 快速开始
        1. 输入项目名称和路径
        2. 选择合适的模板
        3. 配置计算环境
        4. 选择高级功能
        5. 点击创建

        ### 模板说明
        - **llm**: 大语言模型微调
        - **rag**: 检索增强生成
        - **pytorch**: PyTorch 深度学习
        - **inference**: LLM 推理服务
        """)

        st.markdown("---")

        st.markdown("### 💡 提示")
        st.markdown("""
        - 首次使用建议选择默认配置
        - GPU 类型选择"自动检测"最安全
        - Docker 适合部署到生产环境
        - 分布式训练需要多 GPU 支持
        """)

        st.markdown("---")

        st.markdown("""
        ### 🔗 相关链接
        - [GitHub 仓库](https://github.com/YuanyuanMa03/ml-easy-setup)
        - [PyPI 页面](https://pypi.org/project/ml-easy-setup/)
        """)


if __name__ == "__main__":
    main()
