"""
分布式训练配置生成器 - 生成 accelerate 和 DeepSpeed 配置文件
"""

from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from rich.console import Console

console = Console()


@dataclass
class DistributedConfig:
    """分布式配置参数"""
    project_path: Path
    num_gpus: int
    gpu_type: str  # "nvidia" or "amd"
    template_type: str  # "pytorch", "tensorflow", etc.


class DistributedConfigManager:
    """分布式配置管理器"""

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def generate_accelerate_config(
        self,
        num_gpus: int,
        gpu_type: str = "nvidia",
        mixed_precision: str = "bf16"
    ) -> None:
        """
        生成 Accelerate 配置文件

        Args:
            num_gpus: GPU 数量
            gpu_type: GPU 类型 ("nvidia" or "amd")
            mixed_precision: 混合精度类型 ("no", "fp16", "bf16")
        """
        config_path = self.project_path / "accelerate_config.yaml"

        # 根据 GPU 数量和类型选择配置
        if num_gpus == 1:
            distributed_type = "NO"
        elif num_gpus > 1:
            distributed_type = "MULTI_GPU" if gpu_type == "nvidia" else "MULTI_XPU"
        else:
            distributed_type = "CPU"

        # 确定混合精度支持
        precision_map = {
            "nvidia": "bf16",  # NVIDIA GPU 支持 bf16
            "amd": "fp16",    # AMD GPU 通常使用 fp16
            "cpu": "no",
        }
        precision = precision_map.get(gpu_type, "no")

        config_content = f"""compute_environment: LOCAL_MACHINE
distributed_type: {distributed_type}
downcast_bf16: 'no'
machine_rank: 0
main_training_function: main
mixed_precision: {precision}
num_machines: 1
num_processes: {num_gpus}
rdzv_backend: static
same_network: true
tpu_env: []
tpu_use_cluster: false
tpu_use_sudo: false
use_cpu: false

"""
        config_path.write_text(config_content)
        console.print(f"   [dim]生成 accelerate_config.yaml[/dim]")

    def generate_deepspeed_config(
        self,
        num_gpus: int,
        model_size: str = "7b"
    ) -> None:
        """
        生成 DeepSpeed 配置文件

        Args:
            num_gpus: GPU 数量
            model_size: 模型大小 ("7b", "13b", "70b")
        """
        config_path = self.project_path / "ds_config.json"

        # 根据模型大小和 GPU 数量调整配置
        if num_gpus >= 8:
            # 多卡配置：使用 ZeRO Stage 3
            zero_stage = 3
            gradient_accumulation_steps = 1
            train_batch_size = 128
        elif num_gpus >= 4:
            # 中等配置：ZeRO Stage 2-3
            zero_stage = 2
            gradient_accumulation_steps = 2
            train_batch_size = 64
        elif num_gpus >= 2:
            # 双卡配置：ZeRO Stage 2
            zero_stage = 2
            gradient_accumulation_steps = 4
            train_batch_size = 32
        else:
            # 单卡配置：ZeRO Stage 1 + Offload
            zero_stage = 1
            gradient_accumulation_steps = 8
            train_batch_size = 16

        import json

        config = {
            "train_batch_size": train_batch_size,
            "train_micro_batch_size_per_gpu": train_batch_size // num_gpus,
            "gradient_accumulation_steps": gradient_accumulation_steps,
            "optimizer": {
                "type": "AdamW",
                "params": {
                    "lr": "2e-5",
                    "betas": [0.9, 0.999],
                    "eps": 1e-8,
                    "weight_decay": 0.01,
                }
            },
            "scheduler": {
                "type": "WarmupLR",
                "params": {
                    "warmup_min_lr": "0",
                    "warmup_max_lr": "2e-5",
                    "warmup_num_steps": 1000,
                }
            },
            "fp16": {
                "enabled": True,
                "loss_scale": 0,
                "loss_scale_window": 1000,
                "initial_scale_power": 16,
                "hysteresis": 2,
                "min_loss_scale": 1,
            },
            "bf16": {
                "enabled": True,
            },
            "zero_optimization": {
                "stage": zero_stage,
                "overlap_comm": True,
                "contiguous_gradients": True,
                "sub_group_size": 1e9,
                "reduce_bucket_size": 5e8,
                "stage3_prefetch_bucket_size": 5e8,
                "stage3_param_persistence_threshold": 1e5,
                # Stage 3 特定配置
                "stage3_max_live_parameters": 1e9,
                "stage3_param_persistence_threshold": 1e5,
                # 单卡 Offload 配置
                "offload_optimizer": {
                    "device": "cpu" if num_gpus == 1 else "none",
                    "pin_memory": True,
                },
                "offload_param": {
                    "device": "cpu" if num_gpus == 1 else "none",
                    "pin_memory": True,
                },
            },
            "gradient_clipping": 1.0,
            "steps_per_print": 100,
            "wall_clock_breakdown": False,
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        console.print(f"   [dim]生成 ds_config.json (ZeRO Stage {zero_stage})[/dim]")

    def generate_fsdp_config(self, num_gpus: int) -> None:
        """
        生成 FSDP (Fully Sharded Data Parallel) 配置

        Args:
            num_gpus: GPU 数量
        """
        config_path = self.project_path / "fsdp_config.json"

        # 根据卡数选择 sharding strategy
        if num_gpus >= 4:
            sharding_strategy = "FULL_SHARD"  # 最彻底的 sharding
        else:
            sharding_strategy = "SHARD_GRAD_OP"  # 保守的 sharding

        import json

        config = {
            "fsdp_config": {
                "fsdp_transformer_layer_cls_to_wrap": ["LlamaDecoderLayer"],
                "fsdp_backward_prefetch": "BACKWARD_PRE",
                "fsdp_forward_prefetch": False,
                "fsdp_use_orig_params": False,
                "fsdp_cpu_ram_efficient_loading": True,
                "fsdp_auto_wrap_policy": "TRANSFORMER_BASED_WRAP",
                "fsdp_sharding_strategy": sharding_strategy,
                "fsdp_state_dict_type": "SHARDED_STATE_DICT",
                "fsdp_offload_params": num_gpus == 1,  # 单卡启用 CPU offload
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        console.print(f"   [dim]生成 fsdp_config.json ({sharding_strategy})[/dim]")

    def generate_training_script(
        self,
        template_type: str,
        num_gpus: int,
        use_accelerate: bool = True
    ) -> None:
        """
        生成分布式训练启动脚本

        Args:
            template_type: 模板类型
            num_gpus: GPU 数量
            use_accelerate: 是否使用 Accelerate
        """
        scripts_dir = self.project_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        if template_type == "llm" or template_type == "nlp":
            self._generate_llm_training_script(scripts_dir, num_gpus, use_accelerate)
        else:
            self._generate_generic_training_script(scripts_dir, num_gpus, use_accelerate)

    def _generate_llm_training_script(
        self,
        scripts_dir: Path,
        num_gpus: int,
        use_accelerate: bool
    ) -> None:
        """生成 LLM 训练脚本"""
        if use_accelerate:
            script_content = f"""#!/bin/bash
# Accelerate 分布式训练启动脚本

# 设置环境变量
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7

# 单卡训练
accelerate launch \\
    --config_file accelerate_config.yaml \\
    --num_processes={num_gpus} \\
    src/train.py

# 或者使用 torchrun (PyTorch 2.0+)
# torchrun \\
#     --nproc_per_node={num_gpus} \\
#     --master_port=29500 \\
#     src/train.py

# 使用 DeepSpeed
# deepspeed \\
#     --num_gpus={num_gpus} \\
#     src/train.py \\
#     --deepspeed ds_config.json
"""
        else:
            script_content = f"""#!/bin/bash
# DeepSpeed 分布式训练启动脚本

export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7

deepspeed \\
    --num_gpus={num_gpus} \\
    src/train.py \\
    --deepspeed ds_config.json
"""

        script_path = scripts_dir / "train_distributed.sh"
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        console.print(f"   [dim]生成 scripts/train_distributed.sh[/dim]")

    def _generate_generic_training_script(
        self,
        scripts_dir: Path,
        num_gpus: int,
        use_accelerate: bool
    ) -> None:
        """生成通用训练脚本"""
        script_content = f"""#!/bin/bash
# 分布式训练启动脚本

export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7

if [ "{use_accelerate}" = "True" ]; then
    accelerate launch \\
        --config_file accelerate_config.yaml \\
        --num_processes={num_gpus} \\
        src/train.py
else
    torchrun \\
        --nproc_per_node={num_gpus} \\
        --master_port=29500 \\
        src/train.py
fi
"""

        script_path = scripts_dir / "train_distributed.sh"
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        console.print(f"   [dim]生成 scripts/train_distributed.sh[/dim]")

    def generate_multi_gpu_example(self) -> None:
        """生成多 GPU 训练示例代码"""
        example_path = self.project_path / "src" / "train_distributed.py"

        example_code = '''"""
分布式训练示例 - 使用 Accelerate
"""

import torch
from accelerate import Accelerator
from accelerate.utils import set_seed
from torch.utils.data import DataLoader
from transformers import get_linear_schedule_with_warmup
from tqdm import tqdm


def main():
    # 初始化 Accelerator
    accelerator = Accelerator(
        mixed_precision="bf16",
        gradient_accumulation_steps=4,
    )

    # 设置随机种子
    set_seed(42)

    # 创建模型和数据加载器
    # model = create_model()
    # train_loader = create_dataloader()

    # 使用 accelerator 准备模型和数据
    # model, optimizer, train_loader = accelerator.prepare(
    #     model, optimizer, train_loader
    # )

    # 训练循环
    # for epoch in range(num_epochs):
    #     with tqdm(train_loader, desc=f"Epoch {{epoch}}") as pbar:
    #         for batch in pbar:
    #             with accelerator.accumulate(model):
    #                 outputs = model(**batch)
    #                 loss = outputs.loss
    #                 accelerator.backward(loss)
    #                 optimizer.step()
    #                 optimizer.zero_grad()

    #             pbar.set_postfix({"loss": loss.item()})

    # 保存模型
    # accelerator.wait_for_everyone()
    # if accelerator.is_main_process:
    #     unwrapped_model = accelerator.unwrap_model(model)
    #     torch.save(unwrapped_model.state_dict(), "model.pt")

    print(f"Training on {accelerator.num_processes} GPUs")
    print(f"Process {accelerator.process_index}")
    print(f"Device: {accelerator.device}")


if __name__ == "__main__":
    main()
'''
        example_path.write_text(example_code)
        console.print(f"   [dim]生成 src/train_distributed.py[/dim]")

    def generate_launch_config(
        self,
        num_gpus: int,
        template_type: str
    ) -> None:
        """
        生成启动配置文件

        Args:
            num_gpus: GPU 数量
            template_type: 模板类型
        """
        import json

        config = {
            "num_gpus": num_gpus,
            "distributed_type": "accelerate" if template_type in ["llm", "nlp"] else "ddp",
            "launch_command": {
                "accelerate": f"accelerate launch --config_file accelerate_config.yaml --num_processes={num_gpus} src/train.py",
                "deepspeed": f"deepspeed --num_gpus={num_gpus} src/train.py --deepspeed ds_config.json",
                "torchrun": f"torchrun --nproc_per_node={num_gpus} --master_port=29500 src/train.py",
            }
        }

        config_path = self.project_path / "launch_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        console.print(f"   [dim]生成 launch_config.json[/dim]")
