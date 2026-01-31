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
MCLang 跨平台路径管理

提供统一的路径获取接口，支持 Linux、macOS 和 Windows 平台。

路径规范：
- Linux/macOS: ~/.mclang/
- Windows: %LOCALAPPDATA%\\mclang\\

用户可通过环境变量 MCLANG_HOME 自定义安装目录。
"""

import os
import sys
from pathlib import Path
from typing import Optional


def get_mcli_root() -> Path:
    """获取 mcli 安装根目录

    Returns:
        mcli 根目录路径
    """
    # 从 mcli.paths 模块的位置推导
    return Path(__file__).parent.parent


def get_bundled_templates_dir() -> Path:
    """获取打包在 mcli 包内的模板目录

    Returns:
        包内模板目录路径 (mcli/templates/)
    """
    return Path(__file__).parent / "templates"


def get_installed_templates_dir() -> Path:
    """获取已安装的模板目录 (~/.mclang/templates/)

    Returns:
        模板目录路径
    """
    return get_mclang_home() / "templates"


def get_templates_dir() -> Path:
    """获取 mcli 模板目录

    查找优先级：
    1. ~/.mclang/templates/mcli/ - 已安装的模板（版本匹配）
    2. ~/.mclang/templates/ - 兼容旧版本
    3. 源码目录的 templates/ - 开发模式

    Returns:
        模板目录路径

    Note:
        ~/.mclang/templates/ 结构：
        ├── mcli/                    # mcli 自带模板（新版本直接替换）
        │   ├── .version             # 版本文件
        │   ├── conanbase.py.mct
        │   ├── project/
        │   └── toolchain/
        └── thirdparty/              # 三方 project 模板
            └── company-name/        # 命名空间
                ├── .version
                ├── my-service/      # 直接放模板，无 project/ 层
                └── my-lib/
    """
    import importlib.metadata

    # 1. 优先使用已安装的模板目录
    installed_templates_dir = get_installed_templates_dir()

    if installed_templates_dir.exists():
        # 检查 mcli 子目录
        mcli_templates = installed_templates_dir / "mcli"
        if mcli_templates.is_dir() and (mcli_templates / "conanbase.py.mct").exists():
            # 检查版本是否匹配
            version_file = mcli_templates / ".version"
            if version_file.exists():
                try:
                    current_version = importlib.metadata.version("mclang-cli")
                    installed_version = version_file.read_text().strip()

                    if installed_version == current_version:
                        return mcli_templates
                    # 版本不匹配，触发更新
                except importlib.metadata.PackageNotFoundError:
                    pass
            else:
                # 没有 .version 文件，可能是旧版本，直接使用
                return mcli_templates

        # 2. 兼容旧版本：templates 目录直接包含模板文件
        if (installed_templates_dir / "conanbase.py.mct").exists():
            return installed_templates_dir

    # 3. 回退到包内模板目录（开发模式或安装后）
    bundled_templates = get_bundled_templates_dir()
    if bundled_templates.is_dir() and (bundled_templates / "conanbase.py.mct").exists():
        # 尝试自动安装模板
        _install_templates_if_needed()
        # 重新检查已安装目录
        mcli_templates = installed_templates_dir / "mcli"
        if mcli_templates.is_dir() and (mcli_templates / "conanbase.py.mct").exists():
            return mcli_templates
        return bundled_templates

    # 4. 最后的回退
    return bundled_templates


def _install_templates_if_needed() -> None:
    """安装模板到 ~/.mclang/templates/mcli/（如果需要）

    仅在以下情况下安装：
    1. 已安装目录不存在
    2. 版本不匹配（升级时自动更新）

    安装策略：
    - 完全替换 mcli/ 目录
    - 保留 thirdparty/ 目录（三方模板）
    """
    import importlib.metadata
    import shutil

    source_templates = get_bundled_templates_dir()
    if not (source_templates / "conanbase.py.mct").exists():
        return  # 包内模板不存在，跳过安装

    try:
        current_version = importlib.metadata.version("mclang-cli")
        target_dir = get_installed_templates_dir() / "mcli"
        version_file = target_dir / ".version"

        # 检查是否需要安装
        needs_install = False
        if not target_dir.exists():
            needs_install = True
        elif not version_file.exists():
            needs_install = True
        else:
            installed_version = version_file.read_text().strip()
            if installed_version != current_version:
                needs_install = True

        if not needs_install:
            return  # 版本匹配，无需安装

        # 确保父目录存在
        target_dir.parent.mkdir(parents=True, exist_ok=True)

        # 删除旧的 mcli 模板目录
        if target_dir.exists():
            shutil.rmtree(target_dir)

        # 复制模板文件
        shutil.copytree(source_templates, target_dir)

        # 写入版本文件
        version_file.write_text(current_version)

    except (importlib.metadata.PackageNotFoundError, Exception):
        # 静默失败，允许后续代码使用包内模板
        pass


def get_mclang_home() -> Path:
    """获取 MCLang 主目录（跨平台）

    优先级：
    1. 环境变量 MCLANG_HOME
    2. 平台默认路径：
       - Linux/macOS: ~/.mclang
       - Windows: %LOCALAPPDATA%\\mclang

    Returns:
        MCLang 主目录路径
    """
    # 环境变量优先（允许用户自定义）
    if env_home := os.environ.get("MCLANG_HOME"):
        return Path(env_home)

    if sys.platform == "win32":
        # Windows: %LOCALAPPDATA%\mclang
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "mclang"
        else:
            # 回退到用户目录
            return Path.home() / "AppData" / "Local" / "mclang"
    else:
        # Linux/macOS: ~/.mclang
        return Path.home() / ".mclang"


def get_cache_dir() -> Path:
    """获取缓存目录

    用于存放下载的 wheel 文件等临时文件。

    Returns:
        缓存目录路径
    """
    return get_mclang_home() / "cache"


def get_config_file() -> Path:
    """获取全局配置文件路径

    Returns:
        config.toml 文件路径
    """
    return get_mclang_home() / "config.toml"


def ensure_mclang_dirs() -> None:
    """确保 MCLang 目录结构存在

    创建必要的目录：
    - ~/.mclang/
    - ~/.mclang/cache/
    注意：不再创建 ~/.mclang/packages/，packages 由 Conan 管理
    """
    dirs = [
        get_mclang_home(),
        get_cache_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def get_platform_info() -> str:
    """获取平台信息字符串

    Returns:
        平台信息，如 'linux-x86_64', 'macos-arm64', 'windows-x64'
    """
    import platform

    system = sys.platform
    if system == "linux":
        system_name = "linux"
    elif system == "darwin":
        system_name = "macos"
    elif system == "win32":
        system_name = "windows"
    else:
        system_name = system

    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    elif machine in ("i386", "i686", "x86"):
        arch = "x86"
    else:
        arch = machine

    return f"{system_name}-{arch}"


# ============================================================================
# 构建工具路径（支持内置/系统切换）
# ============================================================================

def get_python_executable() -> str:
    """获取 Python 可执行文件路径

    优先级：
    1. 环境变量 MCLANG_PYTHON
    2. 内置 Python（如果存在）：~/.mclang/python/bin/python3
    3. 系统 Python（当前解释器）

    Returns:
        Python 可执行文件路径
    """
    # 环境变量优先
    if env_python := os.environ.get("MCLANG_PYTHON"):
        return env_python

    # 检查内置 Python
    mclang_home = get_mclang_home()
    if sys.platform == "win32":
        builtin_python = mclang_home / "python" / "python.exe"
    else:
        builtin_python = mclang_home / "python" / "bin" / "python3"

    if builtin_python.exists():
        return str(builtin_python)

    # 使用系统 Python
    return sys.executable


def get_meson_executable() -> str:
    """获取 Meson 可执行文件路径

    优先级：
    1. 环境变量 MCLANG_MESON
    2. 内置 meson（如果存在）：~/.mclang/python/bin/meson
    3. 系统 meson（通过 pip 安装）

    Returns:
        Meson 可执行文件路径
    """
    import shutil

    # 环境变量优先
    if env_meson := os.environ.get("MCLANG_MESON"):
        return env_meson

    # 检查内置 meson
    mclang_home = get_mclang_home()
    if sys.platform == "win32":
        builtin_meson = mclang_home / "python" / "Scripts" / "meson.exe"
    else:
        builtin_meson = mclang_home / "python" / "bin" / "meson"

    if builtin_meson.exists():
        return str(builtin_meson)

    # 使用系统 meson
    system_meson = shutil.which("meson")
    if system_meson:
        return system_meson

    # 回退：作为 Python 模块调用
    return f"{get_python_executable()} -m meson"


def get_ninja_executable() -> str:
    """获取 Ninja 可执行文件路径

    优先级：
    1. 环境变量 MCLANG_NINJA
    2. 内置 ninja（如果存在）
    3. 系统 ninja

    Returns:
        Ninja 可执行文件路径
    """
    import shutil

    # 环境变量优先
    if env_ninja := os.environ.get("MCLANG_NINJA"):
        return env_ninja

    # 检查内置 ninja
    mclang_home = get_mclang_home()
    if sys.platform == "win32":
        builtin_ninja = mclang_home / "python" / "Scripts" / "ninja.exe"
    else:
        builtin_ninja = mclang_home / "python" / "bin" / "ninja"

    if builtin_ninja.exists():
        return str(builtin_ninja)

    # 使用系统 ninja
    system_ninja = shutil.which("ninja")
    if system_ninja:
        return system_ninja

    return "ninja"


def is_using_builtin_python() -> bool:
    """检查是否使用内置 Python

    Returns:
        True 如果使用内置 Python
    """
    python_path = get_python_executable()
    mclang_home = str(get_mclang_home())
    return python_path.startswith(mclang_home)


# ============================================================================
# 构建目录路径（支持工具链、目标平台、构建类型）
# ============================================================================

def get_build_dir_name(toolchain: str, target: str, build_type: str) -> str:
    """计算构建目录名称

    Args:
        toolchain: 工具链名称（如 clang, gcc）
        target: 目标平台（如 darwin-arm64, linux-x86_64）
        build_type: 构建类型（Debug 或 Release）

    Returns:
        构建目录名，如 "clang_darwin-arm64_Debug"

    规范：
    - compiler: apple-clang -> clang
    - os: macOS -> darwin
    - arch: x86_64/amd64 -> x86_64, aarch64/arm64/armv8 -> arm64
    - build_type: 首字母大写（debug -> Debug, release -> Release）
    """
    # 规范化工具链名
    compiler = toolchain
    if compiler == 'apple-clang':
        compiler = 'clang'

    build_type_norm = build_type.capitalize()
    return f"{compiler}_{target}_{build_type_norm}"


def get_build_folder_name(project_dir: Path) -> str:
    """从 conanfile.py 读取构建目录名称配置

    Args:
        project_dir: 项目根目录

    Returns:
        构建目录名称，默认为 "builddir"
    """
    try:
        conanfile_path = project_dir / "conanfile.py"
        if not conanfile_path.exists():
            return "builddir"

        with open(conanfile_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 查找 build_folder_name = "xxx"
        import re
        match = re.search(r'build_folder_name\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        return "builddir"
    except Exception:
        return "builddir"


def get_build_dir(project_dir: Path, toolchain: str, target: str, build_type: str) -> Path:
    """计算完整构建目录路径

    Args:
        project_dir: 项目根目录
        toolchain: 工具链名称（如 clang, gcc）
        target: 目标平台（如 darwin-arm64, linux-x86_64）
        build_type: 构建类型（Debug 或 Release）

    Returns:
        完整构建目录路径，如 "/path/to/project/builddir/clang_darwin-arm64_Debug"
    """
    build_folder_name = get_build_folder_name(project_dir)
    build_dir_name = get_build_dir_name(toolchain, target, build_type)
    return project_dir / build_folder_name / build_dir_name


def get_build_config_path(project_dir: Path) -> Path:
    """获取构建配置文件路径（构建目录根目录）

    Args:
        project_dir: 项目根目录

    Returns:
        构建配置文件路径，如 "/path/to/project/builddir/build-config.json"

    Note:
        构建配置放在构建目录根目录，与构建产物同生命周期。
        清理构建目录时，配置也会被删除，避免用户困惑。
    """
    build_folder_name = get_build_folder_name(project_dir)
    return project_dir / build_folder_name / "build-config.json"
