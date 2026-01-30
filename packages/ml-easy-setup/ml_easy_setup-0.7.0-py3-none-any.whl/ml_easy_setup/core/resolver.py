"""
依赖解析器 - 解析和处理包依赖关系
"""

from typing import List, Dict, Set, Optional


class DependencyResolver:
    """依赖解析器"""

    def __init__(self):
        self.conflict_rules = self._load_conflict_rules()

    def _load_conflict_rules(self) -> Dict[str, List[str]]:
        """
        加载已知的冲突规则

        Returns:
            冲突规则字典
        """
        return {
            # PyTorch 和 TensorFlow 的某些版本可能冲突
            "tensorflow": ["torch"],
            # 不同 CUDA 版本的 torch
            "torch+cu118": ["torch+cu121", "torch+cpu"],
            "torch+cu121": ["torch+cu118", "torch+cpu"],
            "torch+cpu": ["torch+cu118", "torch+cu121"],
        }

    def resolve(
        self,
        dependencies: List[str],
        existing_deps: Optional[List[str]] = None
    ) -> List[str]:
        """
        解析依赖关系

        Args:
            dependencies: 需要安装的依赖列表
            existing_deps: 已存在的依赖列表

        Returns:
            解析后的依赖列表
        """
        resolved = set(dependencies)
        existing = set(existing_deps or [])

        # 检查冲突
        conflicts = self._check_conflicts(resolved, existing)
        if conflicts:
            raise DependencyConflictError(
                f"发现依赖冲突: {conflicts}\n"
                f"建议使用不同的环境模板或分离项目"
            )

        return list(resolved)

    def _check_conflicts(
        self,
        new_deps: Set[str],
        existing_deps: Set[str]
    ) -> List[str]:
        """
        检查依赖冲突

        Args:
            new_deps: 新依赖集合
            existing_deps: 已存在依赖集合

        Returns:
            冲突列表
        """
        all_deps = new_deps | existing_deps
        conflicts = []

        for package in all_deps:
            if package in self.conflict_rules:
                conflicting_packages = self.conflict_rules[package]
                for conflicting in conflicting_packages:
                    if any(
                        dep.startswith(conflicting.split("+")[0])
                        for dep in all_deps
                        if dep != package
                    ):
                        conflicts.append(f"{package} 与 {conflicting}")

        return conflicts

    def suggest_resolution(self, conflicts: List[str]) -> List[str]:
        """
        建议冲突解决方案

        Args:
            conflicts: 冲突列表

        Returns:
            解决建议列表
        """
        suggestions = []

        for conflict in conflicts:
            if "torch" in conflict and "tensorflow" in conflict:
                suggestions.append(
                    "建议: PyTorch 和 TensorFlow 不建议在同一环境中使用。\n"
                    "      考虑使用 conda 或为每个框架创建独立环境。"
                )
            elif "cuda" in conflict.lower():
                suggestions.append(
                    "建议: 不同 CUDA 版本的包不能共存。\n"
                    "      选择一个 CUDA 版本，或使用 CPU 版本。"
                )

        return suggestions

    def optimize_install_order(self, dependencies: List[str]) -> List[str]:
        """
        优化安装顺序

        Args:
            dependencies: 依赖列表

        Returns:
            优化后的依赖列表
        """
        # 核心框架优先
        priority_order = [
            "torch",
            "tensorflow",
            "jax",
            "paddlepaddle",
        ]

        ordered = []
        remaining = list(dependencies)

        # 先安装核心框架
        for priority in priority_order:
            for dep in remaining[:]:
                if dep.startswith(priority):
                    ordered.append(dep)
                    remaining.remove(dep)

        # 添加剩余依赖
        ordered.extend(remaining)

        return ordered


class DependencyConflictError(Exception):
    """依赖冲突异常"""

    pass
