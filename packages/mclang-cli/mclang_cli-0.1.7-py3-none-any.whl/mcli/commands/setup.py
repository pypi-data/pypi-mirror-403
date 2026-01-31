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
mcli setup 命令 - 工具链设置向导

引导用户完成 MCLang 工具链的初始设置，包括：
1. 检测系统可用的编译器
2. 引导用户选择或添加工具链
"""

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


def find_system_compilers() -> List[dict]:
    """检测系统可用的编译器

    Returns:
        List[dict]: 可用编译器列表，每个包含 name, path, version
    """
    compilers = []

    # 检查 Clang
    clang = shutil.which("clang")
    if clang:
        try:
            result = subprocess.run(
                [clang, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.split("\n")[0] if result.returncode == 0 else "Unknown"
            compilers.append({
                "name": "clang",
                "path": clang,
                "version": version,
                "type": "system"
            })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # 检查 GCC
    gcc = shutil.which("gcc")
    if gcc:
        try:
            result = subprocess.run(
                [gcc, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split("\n")[0]
                # 检测 macOS 上的 gcc/clang 别名情况
                # macOS 上 "gcc" 通常是 Apple Clang 的别名，应该使用 clang 而不是 gcc
                if "Apple clang" in version_line:
                    # 跳过 macOS 上的 gcc 别名，建议使用 clang
                    print(f"注意: 检测到 'gcc' 是 Apple Clang 的别名 ({version_line})")
                    print("  建议使用 'clang' 工具链而不是 'gcc'")
                else:
                    # 真正的 GCC
                    compilers.append({
                        "name": "gcc",
                        "path": gcc,
                        "version": version_line,
                        "type": "system"
                    })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # 检查 Zig
    zig = shutil.which("zig")
    if zig:
        try:
            result = subprocess.run(
                [zig, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip() if result.returncode == 0 else "Unknown"
            compilers.append({
                "name": "zig",
                "path": zig,
                "version": version,
                "type": "system"
            })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return compilers


def check_toolchains_installed() -> Tuple[bool, str]:
    """检查 mclang 工具链是否已安装

    Returns:
        Tuple[bool, str]: (是否已安装, 状态信息)
    """
    from ..toolchain.manager import get_toolchain_manager

    manager = get_toolchain_manager()
    toolchains = manager.list_toolchains()

    if toolchains:
        return True, f"已配置 {len(toolchains)} 个工具链"
    return False, "未配置任何工具链"


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(num: int, title: str):
    """打印步骤"""
    print(f"\n[{num}] {title}")


def ask_choice(prompt: str, options: List[str], default: int = 0) -> int:
    """询问用户选择

    Args:
        prompt: 提示信息
        options: 选项列表
        default: 默认选项索引

    Returns:
        int: 用户选择的索引
    """
    print(f"\n{prompt}")
    for i, opt in enumerate(options):
        marker = "  " if i == default else "* "
        print(f"{marker}{i + 1}. {opt}")

    while True:
        try:
            response = input(f"选择 [1-{len(options)}] (默认: {default + 1}): ").strip()
            if not response:
                return default
            choice = int(response) - 1
            if 0 <= choice < len(options):
                return choice
            print(f"无效选择，请输入 1-{len(options)}")
        except ValueError:
            print("请输入数字")
        except KeyboardInterrupt:
            print("\n\n操作已取消")
            raise


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    """询问是/否

    Args:
        prompt: 提示信息
        default: 默认值

    Returns:
        bool: 用户选择
    """
    options = ["否", "是"] if not default else ["是", "否"]
    choice = ask_choice(prompt, options, 0 if default else 1)
    return choice == 1


def ask_toolchain_name(compiler_type: str, manager) -> str:
    """询问工具链名称

    Args:
        compiler_type: 编译器类型
        manager: 工具链管理器

    Returns:
        str: 工具链名称
    """
    # 默认名称
    default_name = compiler_type

    # 检查是否已存在
    if manager.toolchain_exists(default_name):
        print(f"\n注意: 工具链 '{default_name}' 已存在")
        print("选项:")
        print("  1. 覆盖现有工具链")
        print("  2. 指定不同的名称")

        choice = input("选择 [1-2] (默认: 2): ").strip()
        if choice == "1":
            return default_name
        else:
            while True:
                name = input(f"输入工具链名称 (留空使用 '{default_name}'): ").strip()
                if not name:
                    return default_name
                if manager.toolchain_exists(name):
                    print(f"工具链 '{name}' 已存在，请选择其他名称")
                else:
                    return name

    return default_name


def run_setup(args) -> bool:
    """运行设置向导"""
    print_header("MCLang 工具链设置向导")
    print("\n此向导将帮助您:")
    print("  1. 检测系统编译器")
    print("  2. 配置 mclang 工具链")
    print("\n按 Ctrl+C 随时退出\n")

    # 步骤 1: 检测系统编译器
    print_step(1, "检测系统编译器")
    compilers = find_system_compilers()

    if compilers:
        print("\n检测到以下编译器:")
        for i, comp in enumerate(compilers):
            print(f"  {i + 1}. {comp['name'].capitalize()} ({comp['version']})")
            print(f"     路径: {comp['path']}")
    else:
        print("\n未检测到系统编译器")
        print("建议安装:")
        print("  - macOS: xcode-select --install")
        print("  - Linux: sudo apt install clang 或 sudo apt install gcc")
        return False

    # 步骤 2: 检查 mclang 工具链
    print_step(2, "检查 mclang 工具链状态")
    from ..toolchain.manager import get_toolchain_manager

    manager = get_toolchain_manager()
    installed, status = check_toolchains_installed()
    print(f"\n{status}")

    if installed:
        toolchains = manager.list_toolchains()
        for tc in toolchains:
            default_marker = " (默认)" if tc.is_default else ""
            print(f"  - {tc.name}{default_marker}: {tc.compiler_type} {tc.compiler_version}")

    # 添加/配置工具链
    if not installed:
        # 没有工具链，需要添加
        if not compilers:
            print("\n错误: 没有可用的编译器")
            return False

        if len(compilers) == 1:
            # 只有一个编译器，自动配置
            selected = compilers[0]
            print(f"\n自动配置工具链: {selected['name']}")
            print(f"  路径: {selected['path']}")

            toolchain_name = selected['name']
            if manager.toolchain_exists(toolchain_name):
                print(f"  注: 工具链 '{toolchain_name}' 已存在，将覆盖")

            print(f"\n配置工具链: {toolchain_name}...")
            try:
                toolchain = manager.add_toolchain(
                    name=toolchain_name,
                    compiler_type=selected['name'],
                )
                print(f"✓ 工具链 '{toolchain_name}' 配置成功")
                print(f"  编译器: {toolchain.compiler_type} {toolchain.compiler_version}")

                # 设置为默认工具链
                try:
                    manager.set_default(toolchain_name)
                    print(f"✓ 已设置为默认工具链")
                except Exception:
                    pass  # 设置默认可能失败，但不影响主流程

            except Exception as e:
                print(f"错误: {e}")
                return False
        else:
            # 多个编译器，让用户选择
            print("\n检测到多个编译器，请选择要配置为工具链的编译器:")
            for i, comp in enumerate(compilers):
                print(f"  {i + 1}. {comp['name'].capitalize()} ({comp['path']})")

            compiler_options = [f"{c['name'].capitalize()} ({c['path']})" for c in compilers]

            choice = ask_choice("选择要配置为工具链的编译器:", compiler_options, default=0)

            if choice < len(compilers):
                selected = compilers[choice]
                print(f"\n选择: {selected['name']}")
                print(f"路径: {selected['path']}")

                toolchain_name = ask_toolchain_name(selected['name'], manager)

                print(f"\n配置工具链: {toolchain_name}...")
                try:
                    toolchain = manager.add_toolchain(
                        name=toolchain_name,
                        compiler_type=selected['name'],
                    )
                    print(f"✓ 工具链 '{toolchain_name}' 配置成功")
                    print(f"  编译器: {toolchain.compiler_type} {toolchain.compiler_version}")

                    # 设置为默认工具链
                    try:
                        manager.set_default(toolchain_name)
                        print(f"✓ 已设置为默认工具链")
                    except Exception:
                        pass

                except Exception as e:
                    print(f"错误: {e}")
                    return False
    elif len(compilers) > 0 and ask_yes_no("\n是否添加新的工具链？", False):
        # 已有工具链，用户想添加新的
        print("\n可用的系统编译器:")
        for i, comp in enumerate(compilers):
            print(f"  {i + 1}. {comp['name'].capitalize()} ({comp['path']})")

        compiler_options = [f"{c['name'].capitalize()} ({c['path']})" for c in compilers]
        compiler_options.append("跳过")

        choice = ask_choice("选择要配置为工具链的编译器:", compiler_options)

        if choice < len(compilers):
            selected = compilers[choice]
            print(f"\n选择: {selected['name']}")
            print(f"路径: {selected['path']}")

            # 检查工具链是否已存在（添加新工具链场景）
            toolchain_name = selected['name']
            if manager.toolchain_exists(toolchain_name):
                print(f"\n注: 工具链 '{toolchain_name}' 已存在，跳过添加")
            else:
                print(f"\n配置工具链: {toolchain_name}...")
                try:
                    toolchain = manager.add_toolchain(
                        name=toolchain_name,
                        compiler_type=selected['name'],
                    )
                    print(f"✓ 工具链 '{toolchain_name}' 添加成功")
                    print(f"  编译器: {toolchain.compiler_type} {toolchain.compiler_version}")

                    # 只有在没有默认工具链时才自动设置
                    if manager.get_default_name() is None:
                        try:
                            manager.set_default(toolchain_name)
                            print(f"✓ 已设置为默认工具链")
                        except Exception:
                            pass

                except Exception as e:
                    print(f"错误: {e}")
                    return False

    # 完成 - 显示工具链列表
    print_header("设置完成")

    toolchains = manager.list_toolchains()
    if toolchains:
        print("\n已配置的工具链:")
        for tc in toolchains:
            default_marker = " (默认)" if tc.is_default else ""
            print(f"  - {tc.name}{default_marker}: {tc.compiler_type} {tc.compiler_version}")
    else:
        print("\n未配置任何工具链")

    return True


def setup_parser(subparsers):
    """设置 setup 命令的参数解析器"""
    setup_parser = subparsers.add_parser(
        "setup",
        help="运行工具链设置向导",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    setup_parser.add_argument(
        "--skip-detect",
        action="store_true",
        help="跳过编译器检测",
    )

    return setup_parser
