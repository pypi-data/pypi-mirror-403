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
Conan Profile 生成器
从 MCLang toolchain 配置生成 Conan profile，确保 mcli build 能正确调用 Conan。
"""


import json
import platform
from pathlib import Path
from typing import Optional, Dict, Any


def get_conan_os_name(system: Optional[str] = None) -> str:
    """将系统名称转换为 Conan 格式

    Args:
        system: 平台名称（如 darwin, linux），None 表示自动检测

    Returns:
        Conan OS 名称（Macos, Linux, Windows）
    """
    if system is None:
        system = platform.system()

    system_lower = system.lower()
    if system_lower in ("darwin", "macos"):
        return "Macos"
    elif system_lower == "linux":
        return "Linux"
    elif system_lower == "windows":
        return "Windows"
    else:
        return system


def get_conan_arch_name(arch: str) -> str:
    """将架构名称转换为 Conan 格式

    Args:
        arch: 架构名称（如 x86_64, arm64, aarch64）

    Returns:
        Conan 架构名称（x86_64, armv8, etc.）
    """
    arch_lower = arch.lower()
    if arch_lower in ("x86_64", "amd64"):
        return "x86_64"
    elif arch_lower in ("aarch64", "arm64"):
        return "armv8"
    elif arch_lower in ("i386", "i686"):
        return "x86"
    else:
        return arch_lower


def get_conan_compiler_name(compiler_type: str, os_name: Optional[str] = None) -> str:
    """将编译器类型转换为 Conan 格式

    Args:
        compiler_type: MCLang 编译器类型（zig, gcc, clang）
        os_name: 操作系统名称（用于区分 apple-clang）

    Returns:
        Conan 编译器类型（gcc, apple-clang, clang）

    Note:
        Zig 编译器使用 clang 作为 Conan 编译器类型，因为 Zig 可以模拟 clang，
        且 Conan 不支持 "zig" 作为有效的 compiler setting。
    """
    compiler_lower = compiler_type.lower()
    if compiler_lower == "gcc":
        return "gcc"
    elif compiler_lower == "clang":
        # macOS 上的 clang 实际上是 apple-clang
        if os_name and os_name.lower() in ("darwin", "macos"):
            return "apple-clang"
        return "clang"
    elif compiler_lower == "zig":
        # Zig 使用 clang 作为 Conan 编译器类型
        # 因为 Zig 可以模拟 clang，且 Conan 不支持 "zig" 作为 compiler setting
        if os_name and os_name.lower() in ("darwin", "macos"):
            return "apple-clang"
        return "clang"
    else:
        return compiler_lower


def _get_system_clang_version() -> str:
    """获取系统 clang 版本

    Returns:
        系统 clang 版本字符串，如果获取失败则返回 "17"
    """
    import subprocess

    try:
        result = subprocess.run(
            ["clang", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            # 输出格式类似: "Apple clang version 15.0.0" 或 "clang version 17.0.1"
            output = result.stdout.strip()
            # 查找版本号
            import re
            match = re.search(r"version\s+(\d+(?:\.\d+)*)", output)
            if match:
                return match.group(1)
    except Exception:
        pass

    # 回退到合理默认值（macOS 上的常见版本）
    return "15"


def generate_conan_profile(
    toolchain_name: str,
    toolchain_path: Path,
    target: str,
    build_type: str,
    project_dir: Optional[Path] = None,
    parallel_jobs: Optional[int] = None,
) -> Path:
    """生成 Conan profile

    Args:
        toolchain_name: 工具链名称（如 clang, zig）
        toolchain_path: 工具链目录路径
        target: 目标平台（如 darwin-arm64）
        build_type: 构建类型（Debug 或 Release）
        project_dir: 项目目录，如果提供则生成项目级 profile（.mclang/conan/profiles/）
                     否则生成全局 profile（~/.mclang/conan/profiles/）
        parallel_jobs: 并行构建任务数，None 表示自动检测（CPU 核心数的 30%）

    Returns:
        生成的 profile 文件路径（包含 build_type）
    """
    from .manager import get_toolchain_manager

    tm = get_toolchain_manager()
    toolchain = tm.get_toolchain(toolchain_name)
    if not toolchain:
        raise ValueError(f"工具链 '{toolchain_name}' 不存在")

    # 加载工具链配置
    config_path = toolchain_path / "config.toml"
    if not config_path.exists():
        raise ValueError(f"工具链配置不存在: {config_path}")

    import tomllib
    with open(config_path, "rb") as f:
        toolchain_config = tomllib.load(f)

    # 解析 target
    target_parts = target.split("-")
    if len(target_parts) >= 2:
        os_name, arch = target_parts[0], target_parts[1]
    else:
        raise ValueError(f"无效的 target 格式: {target}")

    # 转换为 Conan 格式
    conan_os = get_conan_os_name(os_name)
    conan_arch = get_conan_arch_name(arch)
    conan_compiler = get_conan_compiler_name(toolchain.compiler_type, os_name)

    # 获取编译器版本
    compiler_version = toolchain.compiler_version or "unknown"

    # 对于 Zig，使用系统 clang 版本而非 Zig 版本
    # 因为 Zig 使用 clang 作为 Conan compiler setting
    if toolchain.compiler_type == "zig":
        compiler_version = _get_system_clang_version()

    if compiler_version != "unknown":
        # 处理 apple-clang 前缀的版本号（如 apple-clang-17.0.0）
        if compiler_version.startswith("apple-clang-"):
            # 提取版本部分并只保留主版本.次版本（17.0 而非 17.0.0）
            version_part = compiler_version.replace("apple-clang-", "")
            version_parts = version_part.split(".")
            if len(version_parts) >= 2:
                compiler_version = f"{version_parts[0]}.{version_parts[1]}"
            else:
                compiler_version = version_parts[0]
        else:
            # 对于其他编译器，只保留主版本号（如 17）
            compiler_version = compiler_version.split(".")[0]

    # 获取编译器路径
    compiler_path = str(toolchain.compiler_path) if toolchain.compiler_path else ""

    # 获取 C++ 标准
    cpp_std = toolchain_config.get("compiler", {}).get("cpp_std", "c++17")
    # 根据编译器类型转换 cpp_std 格式
    # apple-clang 和 gcc 使用 gnu17 格式，其他使用 17 格式
    if cpp_std.startswith("c++"):
        cpp_std_num = cpp_std.replace("c++", "")
    elif cpp_std.startswith("C++"):
        cpp_std_num = cpp_std.replace("C++", "")
    else:
        cpp_std_num = cpp_std  # 如果已经是 gnu17 等格式，保持不变

    # 对于 apple-clang 和 gcc，需要使用 gnu 前缀
    if conan_compiler in ("apple-clang", "gcc"):
        if not cpp_std_num.startswith("gnu"):
            cpp_std_num = f"gnu{cpp_std_num}"

    # **从工具链配置中提取 build_type 特定的编译参数**
    # 这些参数会被添加到 Conan profile 的 [conf] 节中
    build_type_lower = build_type.lower()
    compiler_args = toolchain_config.get("compiler", {}).get("args", {})
    build_type_args = compiler_args.get(build_type_lower, {})

    # 获取 extra 参数和 defines
    extra_flags = build_type_args.get("extra", [])
    defines = build_type_args.get("defines", [])

    # 获取通用 flags（非 build_type 特定的）
    common_flags = compiler_args.get("flags", [])

    # 获取编译器特定 flags
    # 注意：模板使用 compiler_type (如 "clang") 作为 key，而 Conan 使用 "apple-clang"
    # 需要映射到模板中使用的 key
    compiler_key = conan_compiler
    if conan_compiler == "apple-clang":
        compiler_key = "clang"
    compiler_specific_flags = compiler_args.get(compiler_key, {}).get("flags", [])

    # 合并所有 flags: 通用 flags + 编译器特定 flags + build_type 特定的 extra flags
    all_flags = common_flags + compiler_specific_flags + extra_flags

    # 计算并发度：使用 CPU 核心数的 30%，上下限 1-8
    # 如果用户指定了 parallel_jobs，则使用用户指定的值
    import os
    if parallel_jobs is None:
        cpu_count = os.cpu_count() or 1
        parallel_jobs = max(1, min(8, cpu_count * 30 // 100))
        # 确保至少为 1
        if parallel_jobs < 1:
            parallel_jobs = 1
    else:
        # 用户指定了并发度，验证范围
        if parallel_jobs < 1:
            parallel_jobs = 1
        elif parallel_jobs > 8:
            parallel_jobs = 8

    # 生成 profile 内容（包含 build_type 特定参数）
    profile_content = _generate_profile_content(
        conan_os=conan_os,
        conan_arch=conan_arch,
        conan_compiler=conan_compiler,
        compiler_version=compiler_version,
        compiler_path=compiler_path,
        cpp_std=cpp_std_num,
        build_type=build_type,  # 传递 build_type 到 settings
        toolchain_name=toolchain_name,
        parallel_jobs=parallel_jobs,  # 并发度
        cxx_flags=all_flags,    # 编译参数
        defines=defines,         # 预处理宏
    )

    # 确定输出目录和文件名（包含 build_type）
    profile_name = f"{toolchain_name}-{target}-{build_type_lower}"

    # 如果提供了项目目录，生成项目级 profile
    if project_dir:
        output_dir = project_dir / ".mclang" / "conan" / "profiles"
    else:
        # 否则生成到全局目录
        from ..paths import get_mclang_home
        mclang_home = get_mclang_home()
        output_dir = mclang_home / "conan" / "profiles"

    output_dir.mkdir(parents=True, exist_ok=True)
    profile_path = output_dir / profile_name

    # 写入文件
    profile_path.write_text(profile_content)

    return profile_path


def _generate_profile_content(
    conan_os: str,
    conan_arch: str,
    conan_compiler: str,
    compiler_version: str,
    compiler_path: str,
    cpp_std: str,
    build_type: str,
    toolchain_name: str,
    parallel_jobs: int,
    cxx_flags: list = None,
    defines: list = None,
) -> str:
    """生成 profile 内容（包含 build_type 特定参数）

    Args:
        conan_os: Conan OS 名称
        conan_arch: Conan 架构名称
        conan_compiler: Conan 编译器类型
        compiler_version: 编译器版本
        compiler_path: 编译器路径
        cpp_std: C++ 标准
        build_type: 构建类型（Debug 或 Release）
        toolchain_name: 工具链名称
        parallel_jobs: 并行构建任务数
        cxx_flags: 编译参数列表
        defines: 预处理宏列表
    """
    if cxx_flags is None:
        cxx_flags = []
    if defines is None:
        defines = []

    # 基础配置
    lines = [
        "# MCLang Conan Profile",
        f"# Toolchain: {toolchain_name}",
        f"# Build Type: {build_type}",
        f"# Auto-generated by mcli",
        "",
        "[settings]",
        f"os={conan_os}",
        f"arch={conan_arch}",
        f"compiler={conan_compiler}",
        f"compiler.version={compiler_version}",
        f"compiler.cppstd={cpp_std}",
        f"build_type={build_type}",  # build_type 包含在 profile 中
        "",
    ]

    # 编译器特定配置
    if conan_compiler == "gcc":
        # GCC 使用 libstdc++11
        lines.append("compiler.libcxx=libstdc++11")
    elif conan_compiler in ("clang", "apple-clang"):
        # Clang 使用 libc++
        lines.append("compiler.libcxx=libc++")
    lines.append("")

    # 工具链选项（注释：工具链由 buildenv 中的 CC/CXX 指定）
    # lines.append("[options]")
    # lines.append(f"toolchain={toolchain_name}")
    # lines.append("")

    # 工具路径（如果指定）
    if compiler_path:
        lines.append("[tool_requires]")
        # 对于 Zig，可能需要添加 tool requires
        if conan_compiler == "zig":
            lines.append(f"# zig/{compiler_version}")
        lines.append("")

    # 自定义配置（传递给 conanfile.py）
    lines.append("[conf]")
    lines.append(f"# MCLang toolchain configuration")

    # 并发配置：传入的 parallel_jobs（CPU 核心数的 30% 或用户指定值）
    lines.append(f"tools.build:jobs={parallel_jobs}")
    lines.append(f"# Parallel jobs: {parallel_jobs} (configured by mcli or user)")

    # 添加 build_type 特定的编译参数
    if cxx_flags:
        # 将 flags 列表转换为 JSON 格式（Conan profile 使用 JSON 格式）
        flags_json = json.dumps(cxx_flags)
        lines.append(f"tools.build:cxxflags={flags_json}")

    # 添加预处理宏定义
    if defines:
        # 将 defines 列表转换为 JSON 格式
        defines_json = json.dumps(defines)
        lines.append(f"tools.build:defines={defines_json}")

    lines.append("")

    # 构建环境变量
    lines.append("[buildenv]")
    # 传递工具链名称给 conanfile.py（用于构建目录命名）
    lines.append(f"MCLI_TOOLCHAIN_NAME={toolchain_name}")

    if compiler_path:
        compiler_dir = str(Path(compiler_path).parent)
        compiler_name = Path(compiler_path).name

        # 智能推导 CC 和 CXX 路径
        if toolchain_name == "zig":
            # Zig 使用子命令：zig cc 用于 C，zig c++ 用于 C++
            lines.append(f"CC={compiler_path} cc")
            lines.append(f"CXX={compiler_path} c++")
        elif conan_compiler in ("clang", "apple-clang"):
            # 如果 compiler_path 是 clang++，推导 clang 路径
            if compiler_name.endswith("++"):
                # 去掉末尾的 ++ 得到 C 编译器
                c_compiler_path = str(Path(compiler_path).with_name(compiler_name[:-2]))
                cxx_compiler_path = compiler_path
            else:
                # compiler_path 是 C 编译器，推导 C++ 编译器
                c_compiler_path = compiler_path
                cxx_compiler_path = f"{compiler_path}++"
            lines.append(f"CC={c_compiler_path}")
            lines.append(f"CXX={cxx_compiler_path}")
        elif conan_compiler == "gcc":
            # GCC 类似处理
            if compiler_name.endswith("++"):
                # g++ -> gcc
                c_compiler_path = str(Path(compiler_path).with_name(compiler_name.replace("g++", "gcc")))
                cxx_compiler_path = compiler_path
            else:
                # gcc -> g++
                c_compiler_path = compiler_path
                cxx_compiler_path = str(Path(compiler_path).with_name(compiler_name.replace("gcc", "g++")))
            lines.append(f"CC={c_compiler_path}")
            lines.append(f"CXX={cxx_compiler_path}")
        else:
            # 其他编译器，CC 和 CXX 使用相同路径
            lines.append(f"CC={compiler_path}")
            lines.append(f"CXX={compiler_path}")
    lines.append("")

    return "\n".join(lines)


def get_profile_path(
    toolchain_name: str,
    target: str,
    build_type: str,
    project_dir: Optional[Path] = None,
) -> Path:
    """获取已生成的 profile 路径

    Args:
        toolchain_name: 工具链名称
        target: 目标平台
        build_type: 构建类型（Debug 或 Release）
        project_dir: 项目目录，如果提供则查找项目级 profile

    Returns:
        Profile 文件路径（如果存在）
    """
    profile_name = f"{toolchain_name}-{target}-{build_type.lower()}"

    # 优先查找项目级 profile
    if project_dir:
        project_profile = project_dir / ".mclang" / "conan" / "profiles" / profile_name
        if project_profile.exists():
            return project_profile

    # 回退到全局 profile
    from ..paths import get_mclang_home
    mclang_home = get_mclang_home()
    global_profile = mclang_home / "conan" / "profiles" / profile_name

    if not global_profile.exists():
        raise FileNotFoundError(f"Profile 不存在: {global_profile}")

    return global_profile
