# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# openUBMC is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

"""
mcli run 命令 - 运行 MCLang 项目构建产物

构建参数逻辑：
1. 如果用户指定了 --bt，使用用户指定的参数
2. 否则，检测现有构建配置，使用已保存的参数
3. 如果没有现有构建，使用默认参数 (bt=debug)
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

import tomllib

from ..logging import get_logger
from ..paths import get_build_config_path


@dataclass
class BuildConfig:
    """记录构建配置"""
    build_type: str
    toolchain: str = ""
    target: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "BuildConfig":
        return cls(
            build_type=data.get("build_type", "debug"),
            toolchain=data.get("toolchain", ""),
            target=data.get("target", ""),
        )

    def to_dict(self) -> dict:
        return {
            "build_type": self.build_type,
            "toolchain": self.toolchain,
            "target": self.target,
        }


def load_build_config(project_dir: Path) -> Optional[BuildConfig]:
    """加载已保存的构建配置"""
    config_path = get_build_config_path(project_dir)
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                return BuildConfig.from_dict(data)
        except Exception:
            pass
    return None


def get_targets(mclang_toml: Path) -> List[Dict[str, Any]]:
    """从 mclang.toml 读取 targets 配置"""
    with open(mclang_toml, "rb") as f:
        config = tomllib.load(f)
    return config.get("targets", [])


def find_executable_target(targets: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """查找第一个 executable 类型的目标"""
    for target in targets:
        if target.get("type") == "executable":
            return target
    return None


def find_target_by_name(targets: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    """按名称查找目标"""
    for target in targets:
        if target.get("name") == name:
            return target
    return None


def get_target_path(build_dir: Path, target: Dict[str, Any], build_config: "BuildConfig") -> Optional[Path]:
    """根据目标类型获取可执行文件路径

    Args:
        build_dir: 基础构建目录（通常是 builddir/）
        target: 目标配置
        build_config: 构建配置（包含 toolchain 和 build_type）

    Returns:
        可执行文件路径，如果未找到则返回 None
    """
    name = target.get("name", "")
    target_type = target.get("type", "executable")

    # 优先检查当前 build_dir（可能是工具链特定的目录）
    exe_path = build_dir / name
    if exe_path.exists() and exe_path.is_file():
        return exe_path

    # 如果有 toolchain 信息，直接检查 toolchain 特定的目录
    if build_config.toolchain and build_config.target:
        from ..paths import get_build_dir_name
        toolchain_dir_name = get_build_dir_name(
            build_config.toolchain,
            build_config.target,
            build_config.build_type.capitalize()
        )
        toolchain_build_dir = build_dir / toolchain_dir_name

        exe_path = toolchain_build_dir / name
        if exe_path.exists() and exe_path.is_file():
            return exe_path

        # Meson 子目录
        if target_type == "executable":
            exe_path = toolchain_build_dir / "src" / name
            if exe_path.exists():
                return exe_path
        elif target_type == "test":
            exe_path = toolchain_build_dir / "tests" / name
            if exe_path.exists():
                return exe_path

    # 如果没找到，搜索其他工具链构建目录（向后兼容）
    if build_dir.name == "build":
        build_type_suffix = build_config.build_type.capitalize()
        for subdir in build_dir.iterdir():
            if subdir.is_dir() and subdir.name.endswith(build_type_suffix):
                exe_path = subdir / name
                if exe_path.exists() and exe_path.is_file():
                    return exe_path

    # 回退：检查旧的 build/{Debug|Release}/ 目录结构
    old_build_dir = build_dir.parent / build_config.build_type.capitalize()
    exe_path = old_build_dir / name
    if exe_path.exists() and exe_path.is_file():
        return exe_path

    # 原有 Meson 构建目录
    if target_type == "executable":
        # 可执行程序在 src/{name}
        exe_path = build_dir / "src" / name
        if exe_path.exists():
            return exe_path
        # 也可能直接在 builddir 下
        exe_path = build_dir / name
        if exe_path.exists():
            return exe_path
    elif target_type == "test":
        # 测试程序在 tests/{name}
        exe_path = build_dir / "tests" / name
        if exe_path.exists():
            return exe_path
        # 也可能直接在 builddir 下
        exe_path = build_dir / name
        if exe_path.exists():
            return exe_path

    # Windows 支持
    for path in [build_dir / "src" / f"{name}.exe",
                 build_dir / "tests" / f"{name}.exe",
                 build_dir / f"{name}.exe"]:
        if path.exists():
            return path

    return None


def run_run(args) -> bool:
    """运行项目构建产物

    构建参数逻辑：
    1. 如果用户指定了 --bt，使用用户指定的参数
    2. 否则，检测现有构建配置，使用已保存的参数
    3. 如果没有现有构建，使用默认参数 (bt=debug)
    """
    from .build import run_build

    project_dir = Path.cwd()

    # 获取日志记录器（使用默认 debug build_type，稍后会根据实际构建配置更新）
    logger = get_logger("run", project_dir, "debug")

    # 检查 mclang.toml 是否存在
    mclang_toml = project_dir / "mclang.toml"
    if not mclang_toml.exists():
        logger.error("未找到 mclang.toml，请在 MCLang 项目目录中运行此命令")
        return False

    # 检查 conanfile.py 是否存在
    conanfile = project_dir / "conanfile.py"
    if not conanfile.exists():
        logger.error("未找到 conanfile.py")
        logger.info("提示: MCLang 项目需要使用 Conan 构建系统")
        return False

    # === 确定构建参数 ===
    # 优先级：用户指定 > 现有构建配置 > 默认值
    user_specified_bt = getattr(args, "bt", None)

    if user_specified_bt:
        # 用户显式指定了参数
        build_type = user_specified_bt
        build_config = BuildConfig(build_type=build_type)
    else:
        # 读取现有构建配置
        existing_config = load_build_config(project_dir)
        if existing_config:
            build_config = existing_config
        else:
            # 使用默认值
            build_config = BuildConfig(build_type="debug")

    # === 构建项目 ===
    class BuildArgs:
        bt = build_config.build_type
        verbose = getattr(args, "verbose", False)
        # 优先使用用户指定的 toolchain，否则使用 build_config 中保存的 toolchain
        target = getattr(args, "target", None) or build_config.target or None
        toolchain = getattr(args, "toolchain", None) or build_config.toolchain or None

    if not run_build(BuildArgs()):
        return False

    # === 查找并运行可执行文件 ===
    # 读取 targets 配置
    targets = get_targets(mclang_toml)

    if not targets:
        logger.error("mclang.toml 中未定义 [[targets]]")
        logger.error("提示: 请在 mclang.toml 中添加构建目标配置")
        return False

    # 查找要运行的目标
    target_name = getattr(args, "target", None)

    if target_name:
        # 按名称查找
        target = find_target_by_name(targets, target_name)
        if not target:
            logger.error(f"未找到目标 '{target_name}'")
            logger.error("可用目标:")
            for t in targets:
                logger.error(f"  {t.get('name')} ({t.get('type')})")
            return False
    else:
        # 查找第一个 executable 目标
        target = find_executable_target(targets)
        if not target:
            # 如果没有 executable，使用第一个目标
            target = targets[0]
            logger.info(f"提示: 未找到 executable 目标，使用 '{target.get('name')}'")

    # 确定构建目录（使用可配置的构建目录名，get_target_path 会查找工具链特定子目录）
    from ..paths import get_build_folder_name
    build_folder_name = get_build_folder_name(project_dir)
    build_dir = project_dir / build_folder_name

    # 获取可执行文件路径（传递完整 build_config 以支持 toolchain 特定目录查找）
    exe_path = get_target_path(build_dir, target, build_config)

    if not exe_path:
        logger.error(f"未找到目标 '{target.get('name')}' 的可执行文件")
        logger.error(f"提示: 请确保项目已构建成功")
        return False

    # 运行
    logger.info(f"运行: {target.get('name')}")

    # 传递额外参数给可执行文件
    extra_args = getattr(args, "args", []) or []
    run_args = [str(exe_path)] + extra_args

    result = subprocess.run(run_args, cwd=project_dir)
    return result.returncode == 0
