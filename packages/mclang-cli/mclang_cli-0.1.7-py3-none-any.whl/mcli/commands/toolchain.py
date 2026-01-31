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
mcli toolchain 命令

管理 mclang 工具链

面向最终用户的工具链管理命令：
- mcli toolchain list: 查看所有工具链
- mcli toolchain add: 添加工具链（使用系统已安装的编译器）
- mcli toolchain remove: 移除工具链
- mcli toolchain set-default: 设置默认工具链
- mcli toolchain info: 显示工具链详细信息

注意：mclang 使用用户系统已安装的编译器（如 gcc, clang, zig），
不提供独立的工具链包。用户需要自行安装编译器。

Copyright (c) 2026 Huawei Technologies Co., Ltd.
openUBMC is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
See the Mulan PSL v2 for more details.
"""

import argparse
from pathlib import Path


def run_toolchain(args) -> bool:
    """toolchain 命令主入口"""
    subcommand = getattr(args, "toolchain_command", None)

    if subcommand == "list":
        return cmd_list(args)
    elif subcommand == "add":
        return cmd_add(args)
    elif subcommand == "remove":
        return cmd_remove(args)
    elif subcommand == "set-default":
        return cmd_set_default(args)
    elif subcommand == "info":
        return cmd_info(args)
    else:
        print("用法: mcli toolchain <command>")
        print("")
        print("可用命令:")
        print("  list          查看所有工具链")
        print("  add           添加工具链")
        print("  remove        移除工具链")
        print("  set-default   设置默认工具链")
        print("  info          显示工具链详细信息")
        return True


def cmd_list(args) -> bool:
    """显示所有工具链"""
    from mcli import __version__ as mcli_version
    from ..toolchain.manager import get_toolchain_manager
    from ..toolchain.base import get_host_target

    print(f"MCLang {mcli_version}")
    print("")

    # 主机平台
    host = get_host_target()
    print(f"主机平台: {host}")
    print("")

    # 工具链列表
    manager = get_toolchain_manager()
    toolchains = manager.list_toolchains()

    if not toolchains:
        print("未配置任何工具链")
        print("  使用 'mcli toolchain add <compiler>' 添加工具链")
        return True

    print("工具链:")
    for tc in toolchains:
        default_marker = " (默认)" if tc.is_default else ""
        print(f"  {tc.name}{default_marker}")
        print(f"    编译器: {tc.compiler_type} {tc.compiler_version}")

    return True


def cmd_add(args) -> bool:
    """添加工具链"""
    from ..toolchain.manager import get_toolchain_manager, ToolchainError
    from ..toolchain.toolchain import COMPILER_GCC, COMPILER_CLANG, COMPILER_ZIG

    compiler_type = args.compiler
    name = getattr(args, "name", None)
    compiler_path = getattr(args, "path", None)
    set_as_default = getattr(args, "set_default", False)
    force = getattr(args, "force", False)

    manager = get_toolchain_manager()

    # 默认工具链名称 = 编译器类型
    if name is None:
        name = compiler_type

    # 检查名称冲突
    if manager.toolchain_exists(name) and not force:
        existing = manager.get_toolchain(name)
        if existing:
            print(f"错误: 工具链 '{name}' 已存在")
            print(f"  编译器: {existing.compiler_type} {existing.compiler_version}")
            print("")
            print("解决方案:")
            print(f"  1. 使用 --name 指定不同的名称")
            print(f"  2. 使用 --force 覆盖现有工具链")
            return False

    try:
        toolchain = manager.add_toolchain(
            name=name,
            compiler_type=compiler_type,
            compiler_path=Path(compiler_path) if compiler_path else None,
            set_as_default=set_as_default,
            force=force,
        )

        print(f"✓ 工具链 '{name}' 添加成功")
        print(f"  编译器: {toolchain.compiler_type} {toolchain.compiler_version}")
        if set_as_default:
            print(f"  已设为默认工具链")

        return True

    except ToolchainError as e:
        print(f"错误: {e}")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False


def cmd_remove(args) -> bool:
    """移除工具链"""
    from ..toolchain.manager import get_toolchain_manager

    name = args.name

    manager = get_toolchain_manager()

    if not manager.toolchain_exists(name):
        print(f"工具链 '{name}' 不存在")
        return False

    if manager.remove_toolchain(name):
        print(f"✓ 工具链 '{name}' 已移除")
        return True
    else:
        print(f"移除工具链 '{name}' 失败")
        return False


def cmd_set_default(args) -> bool:
    """设置默认工具链"""
    from ..toolchain.manager import get_toolchain_manager

    name = args.name

    manager = get_toolchain_manager()

    if not manager.toolchain_exists(name):
        print(f"工具链 '{name}' 不存在")
        return False

    if manager.set_default(name):
        print(f"✓ 默认工具链已设置为 '{name}'")
        return True
    else:
        print(f"设置默认工具链失败")
        return False


def cmd_info(args) -> bool:
    """显示工具链详细信息"""
    from mcli import __version__ as mcli_version
    from ..toolchain.manager import get_toolchain_manager
    from ..paths import get_mclang_home

    name = args.name

    manager = get_toolchain_manager()
    toolchain = manager.get_toolchain(name)

    if not toolchain:
        print(f"工具链 '{name}' 不存在")
        return False

    print(f"MCLang {mcli_version} - 工具链详情")
    print("=" * 50)
    print("")

    print(f"名称: {toolchain.name}")
    print(f"目录: {toolchain._toolchain_dir}")
    print("")

    manifest = toolchain.manifest
    if manifest:
        print("编译器:")
        print(f"  类型: {manifest.compiler_type}")
        print(f"  版本: {manifest.compiler_version}")
        if manifest.compiler_path:
            print(f"  路径: {manifest.compiler_path}")
        print(f"  宿主: {manifest.host}")
    print("")

    print("")

    # 工具链配置
    config = toolchain.get_config()
    if config:
        print("工具链配置:")
        import json
        print(json.dumps(config, indent=2, ensure_ascii=False))
    else:
        print("工具链配置: (默认配置)")

    return True


def setup_parser(subparsers) -> argparse.ArgumentParser:
    """设置 toolchain 子命令解析器"""
    parser = subparsers.add_parser(
        "toolchain",
        help="管理编译工具链",
    )

    toolchain_subparsers = parser.add_subparsers(
        dest="toolchain_command",
        help="工具链命令",
    )

    # list 命令
    toolchain_subparsers.add_parser(
        "list",
        help="查看所有工具链",
    )

    # add 命令
    add_parser = toolchain_subparsers.add_parser(
        "add",
        help="添加工具链",
    )
    add_parser.add_argument(
        "compiler",
        choices=["gcc", "clang", "zig"],
        help="编译器类型",
    )
    add_parser.add_argument(
        "--name",
        help="工具链名称（默认为编译器类型）",
    )
    add_parser.add_argument(
        "--path",
        help="编译器所在目录或完整路径",
    )
    add_parser.add_argument(
        "--set-default",
        action="store_true",
        help="添加后设为默认工具链",
    )
    add_parser.add_argument(
        "--force",
        action="store_true",
        help="覆盖已存在的工具链",
    )

    # remove 命令
    remove_parser = toolchain_subparsers.add_parser(
        "remove",
        help="移除工具链",
    )
    remove_parser.add_argument(
        "name",
        help="工具链名称",
    )

    # set-default 命令
    set_default_parser = toolchain_subparsers.add_parser(
        "set-default",
        help="设置默认工具链",
    )
    set_default_parser.add_argument(
        "name",
        help="工具链名称",
    )

    # info 命令
    info_parser = toolchain_subparsers.add_parser(
        "info",
        help="显示工具链详细信息",
    )
    info_parser.add_argument(
        "name",
        help="工具链名称",
    )

    return parser
