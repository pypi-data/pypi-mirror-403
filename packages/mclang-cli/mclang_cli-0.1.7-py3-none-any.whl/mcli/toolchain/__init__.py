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
MCLang 工具链管理模块
提供编译器类型常量和目标平台信息。
工具链由外部安装，mcli 负责管理和配置已安装的工具链。
"""


from .base import (
    ToolchainError,
    # 编译器类型常量
    COMPILER_ZIG,
    COMPILER_GCC,
    COMPILER_CLANG,
    # 支持的目标平台
    SUPPORTED_TARGETS,
    COMPILER_TARGET_MAP,
    DEFAULT_BINARIES_TEMPLATES,
    # 工具函数
    get_host_target,
    get_compiler_target,
)
from .manager import ToolchainManager, get_default_toolchain, get_toolchain_manager
from .toolchain import Toolchain as ToolchainInstance, ToolchainManifest

__all__ = [
    # 基础类
    "ToolchainError",
    # 编译器常量
    "COMPILER_ZIG",
    "COMPILER_GCC",
    "COMPILER_CLANG",
    # 目标平台
    "SUPPORTED_TARGETS",
    "COMPILER_TARGET_MAP",
    "DEFAULT_BINARIES_TEMPLATES",
    "get_host_target",
    "get_compiler_target",
    # 管理器
    "ToolchainManager",
    "get_default_toolchain",
    "get_toolchain_manager",
    # 工具链实例
    "ToolchainInstance",
    "ToolchainManifest",
]
