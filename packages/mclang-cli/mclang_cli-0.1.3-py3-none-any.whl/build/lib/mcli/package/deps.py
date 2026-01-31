#!/usr/bin/env python3
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
mcli 依赖管理工具模块
功能：
1. 解析和修改 service.json 依赖配置
2. 安装 Conan 包
3. 同步 .mclang/ 目录（创建 stub 软链接）
"""


import json
import os
import shutil
import subprocess
from pathlib import Path
from argparse import Namespace
from typing import Dict, List, Optional, Any

from mcli.config import load_project_config
from mcli.logging import get_logger


SERVICE_JSON_PATH = "mds/service.json"


def parse_conan_ref(ref: str) -> tuple[str, str, str, str]:
    """解析 Conan 引用，返回 (name, version, user, channel)"""
    if "@" in ref:
        package_part, user_channel = ref.split("@", 1)
        if "/" in user_channel:
            user, channel = user_channel.split("/", 1)
        else:
            user, channel = user_channel, "unknown"
    else:
        package_part = ref
        user, channel = "", ""

    if "/" in package_part:
        name, version = package_part.split("/", 1)
    else:
        name, version = package_part, "0.0.0"

    return name, version, user, channel


def get_dependencies(project_dir: Path, dep_type: str = "test") -> List[str]:
    """获取项目依赖列表

    Args:
        project_dir: 项目目录
        dep_type: 依赖类型 ("test" 或 "build")

    Returns:
        Conan 依赖引用列表（如 ["mcl_runtime/0.1.0@user/dev"]）
    """
    config = load_project_config(project_dir)
    return config.get_conan_dependencies(dep_type)


def add_dependency(
    project_dir: Path,
    conan_ref: str,
    dep_type: str = "test",
    logger=None
) -> bool:
    if logger is None:
        logger = get_logger("deps", project_dir, "debug")

    service_path = project_dir / SERVICE_JSON_PATH
    if not service_path.exists():
        logger.error(f"未找到 {SERVICE_JSON_PATH}")
        return False

    with open(service_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if "dependencies" not in config:
        config["dependencies"] = {}
    if dep_type not in config["dependencies"]:
        config["dependencies"][dep_type] = []

    deps = config["dependencies"][dep_type]

    # 检查是否已存在
    for dep in deps:
        if dep.get("conan") == conan_ref:
            logger.info(f"  依赖已存在: {conan_ref}")
            return True

    # 添加依赖
    deps.append({"conan": conan_ref})

    with open(service_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    return True


def remove_dependency(
    project_dir: Path,
    package_name: str,
    dep_type: str = "test"
) -> bool:
    """从 service.json 移除依赖

    Args:
        project_dir: 项目目录
        package_name: 包名（如 "mcl_runtime"）
        dep_type: 依赖类型 ("test" 或 "build")

    Returns:
        是否成功
    """
    service_path = project_dir / SERVICE_JSON_PATH
    if not service_path.exists():
        return False

    with open(service_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if "dependencies" not in config or dep_type not in config["dependencies"]:
        return False

    deps = config["dependencies"][dep_type]
    original_length = len(deps)

    # 移除匹配的依赖（按包名匹配）
    config["dependencies"][dep_type] = [
        dep for dep in deps
        if package_name not in dep.get("conan", "")
    ]

    if len(config["dependencies"][dep_type]) == original_length:
        return False  # 没有找到要删除的依赖

    with open(service_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    return True


def install_conan_package(
    project_dir: Path,
    conan_ref: str,
    profile: Optional[Path] = None,
    logger=None
) -> bool:
    """安装 Conan 包（Conan 自动处理已安装包的检测）"""
    if logger is None:
        logger = get_logger("deps", project_dir, "debug")

    logger.info(f"  安装 {conan_ref}...")

    cmd = ["conan", "install", "--requires", conan_ref]
    if profile:
        cmd.extend(["-pr:h", str(profile)])

    result = subprocess.run(cmd, cwd=project_dir, capture_output=True)
    if result.returncode != 0:
        logger.warning(f"  conan install 失败: {result.stderr.decode()}")
        return False

    logger.info(f"  ✓ {conan_ref} 已安装")
    return True


def install_conan_packages_for_project(
    project_dir: Path,
    dep_type: str = "test",
    profile: Optional[Path] = None,
    verbose: bool = False,
) -> bool:
    """为项目安装所有 Conan 依赖

    Args:
        project_dir: 项目目录
        dep_type: 依赖类型 ("test" 或 "build")
        profile: Conan profile 路径
        verbose: 是否显示详细输出

    Returns:
        是否全部成功
    """
    deps = get_dependencies(project_dir, dep_type)
    if not deps:
        return True  # 没有依赖

    all_success = True
    for conan_ref in deps:
        success = install_conan_package(project_dir, conan_ref, profile)
        if not success:
            all_success = False

    return all_success


def sync_mclang_dir(project_dir: Path, profile_path: Optional[Path] = None, dep_type: str = "test", verbose: bool = False, logger=None, build_type: str = "debug") -> bool:
    """同步项目 stub 包到 .mclang/packages/ 目录

    创建顶级包链接（如 mc、gtest），支持直接 `from mc import main` 导入，
    而无需 `from mcl_runtime.mc import main`。

    Args:
        project_dir: 项目目录
        profile_path: Conan profile 路径（如果未提供，将尝试从项目查找）
        dep_type: 依赖类型 ("test" 或 "build")
        verbose: 是否显示详细输出
        logger: 日志记录器

    Returns:
        是否成功同步
    """
    from mcli.package.conan import (
        get_project_packages,
        get_package_path,
        get_package_stubs_config,
        get_package_stubs_dir,
    )

    if logger is None:
        logger = get_logger("deps", project_dir, "debug")

    mclang_dir = project_dir / ".mclang"
    packages_dir = mclang_dir / "packages"

    # 确保目录存在
    mclang_dir.mkdir(exist_ok=True)
    packages_dir.mkdir(exist_ok=True)

    # 收集所有需要的 stub 包
    needed_stub_links = {}  # {link_name: source_path}

    # 使用 conan graph info 获取 Conan 实际选择的包
    # 如果是测试依赖，需要传递 -o *:test=True 选项
    is_test_mode = (dep_type == "test")
    pkg_refs = get_project_packages(project_dir, profile_path=profile_path, test=is_test_mode, build_type=build_type)

    for pkg_ref in pkg_refs:
        # 获取包路径
        source_path = get_package_path(pkg_ref)
        if not source_path:
            if verbose:
                logger.warning(f"  找不到 package '{pkg_ref.name}'")
            continue

        # 检查是否是 Conan 缓存包（包含 stubs 目录）
        # 从 package 中读取 stubs 配置（支持多个路径）
        stubs_config = get_package_stubs_config(source_path)
        stubs_base_dir = get_package_stubs_dir(source_path)

        if stubs_base_dir:
            # 优先使用配置中的 stub 包列表，否则扫描目录
            if stubs_config:
                # 从 mclang.json 读取的配置
                stub_pkgs = stubs_config.get("packages", [])
            else:
                # 回退：扫描 stubs 目录，查找所有 Python 包
                stub_pkgs = []
                for item in stubs_base_dir.iterdir():
                    if item.is_dir() and (item / "__init__.py").exists():
                        stub_pkgs.append(item.name)

            # 为每个 stub 包创建软链接
            for stub_pkg in stub_pkgs:
                stub_source = stubs_base_dir / stub_pkg
                if stub_source.exists():
                    link_name = stub_pkg  # 使用 stub 包名作为链接名
                    needed_stub_links[link_name] = stub_source
                    if verbose:
                        logger.debug(f"  发现 stub: {link_name} <- {pkg_ref.name}/{pkg_ref.version}")

    # 获取当前 packages/ 中的链接
    existing_links = set()
    if packages_dir.exists():
        for item in packages_dir.iterdir():
            existing_links.add(item.name)

    # 移除不再需要的链接
    for link_name in existing_links - set(needed_stub_links.keys()):
        link_path = packages_dir / link_name
        if link_path.is_symlink() or link_path.exists():
            if link_path.is_symlink():
                link_path.unlink()
            elif link_path.is_dir():
                shutil.rmtree(link_path)
            else:
                link_path.unlink()
            if verbose:
                logger.debug(f"  移除 {link_name}")

    # 创建/更新需要的链接
    synced = 0
    for link_name, source_path in needed_stub_links.items():
        link_path = packages_dir / link_name

        # 检查是否需要更新
        need_update = False
        if link_path.is_symlink():
            current_target = link_path.resolve()
            if current_target != source_path.resolve():
                need_update = True
                link_path.unlink()
        elif link_path.exists():
            # 是普通目录/文件，删除
            shutil.rmtree(link_path)
            need_update = True
        else:
            need_update = True

        if need_update:
            # 创建软链接
            try:
                link_path.symlink_to(source_path)
                if verbose:
                    logger.debug(f"  链接 {link_name} → {source_path}")
            except OSError as e:
                # Windows 可能不支持软链接，使用复制
                logger.warning(f"  软链接失败，使用复制: {e}")
                shutil.copytree(source_path, link_path)
                if verbose:
                    logger.debug(f"  复制 {link_name} ← {source_path}")
            synced += 1

    return synced > 0 or len(existing_links - set(needed_stub_links.keys())) > 0
