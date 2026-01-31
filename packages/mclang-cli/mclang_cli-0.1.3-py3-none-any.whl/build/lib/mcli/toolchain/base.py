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
工具链基础定义
提供编译器类型常量和目标平台信息。
"""


import sys
import platform
from typing import List, Optional, Dict, Any


class ToolchainError(Exception):
    """工具链错误"""
    pass


# ============================================================================
# 编译器类型常量
# ============================================================================
COMPILER_ZIG = "zig"
COMPILER_GCC = "gcc"
COMPILER_CLANG = "clang"


# ============================================================================
# 支持的目标平台（与编译器无关的通用信息）
# ============================================================================
SUPPORTED_TARGETS: Dict[str, Dict] = {
    "linux-x86_64": {
        "triple": "x86_64-linux-gnu",
        "lib_suffix": ".so",
        "exe_suffix": "",
        "description": "Linux x86_64 (glibc)",
    },
    "linux-aarch64": {
        "triple": "aarch64-linux-gnu",
        "lib_suffix": ".so",
        "exe_suffix": "",
        "description": "Linux ARM64 (glibc)",
    },
    "darwin-arm64": {
        "triple": "aarch64-apple-darwin",
        "lib_suffix": ".dylib",
        "exe_suffix": "",
        "description": "macOS ARM64 (Apple Silicon)",
    },
    "darwin-x86_64": {
        "triple": "x86_64-apple-darwin",
        "lib_suffix": ".dylib",
        "exe_suffix": "",
        "description": "macOS x86_64 (Intel)",
    },
    "wasm32-wasi": {
        "triple": "wasm32-wasi",
        "lib_suffix": ".wasm",
        "exe_suffix": ".wasm",
        "description": "WebAssembly (WASI)",
    },
}


# ============================================================================
# 各编译器的目标平台字符串映射
# ============================================================================
# 不同编译器对同一平台有不同的目标字符串格式
# 值为 None 表示该编译器不支持此目标
COMPILER_TARGET_MAP: Dict[str, Dict[str, Optional[str]]] = {
    "linux-x86_64": {
        COMPILER_ZIG: "x86_64-linux-gnu",
        COMPILER_GCC: "x86_64-linux-gnu",
        COMPILER_CLANG: "x86_64-linux-gnu",
    },
    "linux-aarch64": {
        COMPILER_ZIG: "aarch64-linux-gnu",
        COMPILER_GCC: "aarch64-linux-gnu",
        COMPILER_CLANG: "aarch64-linux-gnu",
    },
    "darwin-arm64": {
        COMPILER_ZIG: "aarch64-macos",
        COMPILER_GCC: "aarch64-apple-darwin",
        COMPILER_CLANG: "arm64-apple-darwin",
    },
    "darwin-x86_64": {
        COMPILER_ZIG: "x86_64-macos",
        COMPILER_GCC: "x86_64-apple-darwin",
        COMPILER_CLANG: "x86_64-apple-darwin",
    },
    "wasm32-wasi": {
        COMPILER_ZIG: "wasm32-wasi",
        COMPILER_GCC: None,  # GCC 不支持 WASM
        COMPILER_CLANG: "wasm32-wasi",
    },
}


# ============================================================================
# 默认二进制文件模板（用于工具链配置）
# ============================================================================
# 当工具链配置未指定 [binaries] 时使用的默认模板
# 模板变量: {compiler_path}, {compiler_dir}, {target}, {triple}
# ============================================================================
DEFAULT_BINARIES_TEMPLATES: Dict[str, Dict[str, Any]] = {
    COMPILER_ZIG: {
        "c": ["{compiler_path}", "cc"],
        "cpp": ["{compiler_path}", "c++"],
        "ar": ["{compiler_path}", "ar"],
        "ranlib": ["{compiler_path}", "ranlib"],
        "cross": {
            "c": ["{compiler_path}", "cc", "-target", "{target}"],
            "cpp": ["{compiler_path}", "c++", "-target", "{target}"],
            "ar": ["{compiler_path}", "ar"],
            "ranlib": ["{compiler_path}", "ranlib"],
        }
    },
    COMPILER_GCC: {
        "c": "{compiler_dir}/gcc",
        "cpp": "{compiler_dir}/g++",
        "ar": "{compiler_dir}/ar",
        "ranlib": "{compiler_dir}/ranlib",
        "cross": {
            "c": "{compiler_dir}/{triple}-gcc",
            "cpp": "{compiler_dir}/{triple}-g++",
            "ar": "{compiler_dir}/{triple}-ar",
            "ranlib": "{compiler_dir}/{triple}-ranlib",
        }
    },
    COMPILER_CLANG: {
        "c": "{compiler_dir}/clang",
        "cpp": "{compiler_dir}/clang++",
        "ar": "ar",
        "ranlib": "ranlib",
        "cross": {
            "c": ["{compiler_dir}/clang", "-target", "{target}"],
            "cpp": ["{compiler_dir}/clang++", "-target", "{target}"],
            "ar": "ar",
            "ranlib": "ranlib",
        }
    },
}


def get_host_target() -> str:
    """获取当前主机的目标平台

    Returns:
        mclang 平台标识，如 'linux-x86_64', 'darwin-arm64'
    """
    system = sys.platform
    machine = platform.machine().lower()

    if system == "darwin":
        if machine in ("arm64", "aarch64"):
            return "darwin-arm64"
        else:
            return "darwin-x86_64"
    elif system.startswith("linux"):
        if machine in ("arm64", "aarch64"):
            return "linux-aarch64"
        else:
            return "linux-x86_64"
    else:
        return f"{system}-{machine}"


def get_compiler_target(target: str, compiler_type: str) -> Optional[str]:
    """获取特定编译器的目标字符串

    Args:
        target: mclang 平台标识，如 'linux-x86_64'
        compiler_type: 编译器类型，如 'zig', 'gcc', 'clang'

    Returns:
        编译器特定的目标字符串，如 'x86_64-linux-gnu'
        如果编译器不支持该目标，返回 None
    """
    if target not in COMPILER_TARGET_MAP:
        return None
    return COMPILER_TARGET_MAP[target].get(compiler_type)
