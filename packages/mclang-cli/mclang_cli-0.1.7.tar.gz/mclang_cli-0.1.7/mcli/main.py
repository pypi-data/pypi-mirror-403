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
MCLang CLI 入口点

mcli - MCLang 项目管理工具
"""

import sys
import argparse
from pathlib import Path

from . import __version__


def cmd_build(args):
    """构建项目"""
    from .commands.build import run_build

    return run_build(args)


def cmd_install(args):
    """安装 Package"""
    from .commands.install import run_install

    return run_install(args)


def cmd_reload_deps(args):
    """刷新依赖"""
    from .commands.reload_deps import run_reload_deps

    return run_reload_deps(args)


def cmd_publish(args):
    """发布 Package 到 PyPI"""
    from .commands.publish import run_publish

    return run_publish(args)


def cmd_test(args):
    """运行项目测试"""
    from .commands.test import run_test

    return run_test(args)


def cmd_run(args):
    """运行项目构建产物"""
    from .commands.run import run_run

    return run_run(args)


def cmd_toolchain(args):
    """管理工具链"""
    from .commands.toolchain import run_toolchain

    return run_toolchain(args)


def cmd_config(args):
    """管理配置"""
    from .commands.config import run_config

    return run_config(args)


def cmd_create(args):
    """从模板创建项目"""
    from .commands.create import run_create

    return run_create(args)


def cmd_setup(args):
    """运行工具链设置向导"""
    from .commands.setup import run_setup

    return run_setup(args)


def cmd_clean(args):
    """清理项目构建产物"""
    from .commands.clean import run_clean

    return run_clean(args)


def cmd_cache(args):
    """管理 Conan 包缓存"""
    from .commands.cache import run_cache

    return run_cache(args)


def main():
    """mcli 命令行入口点"""
    parser = argparse.ArgumentParser(
        prog="mcli",
        description="MCLang CLI - MCLang 项目管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
命令:
  create         从模板创建 MCLang 项目
  setup          运行工具链设置向导
  build          构建项目
  test           运行项目测试
  run            运行项目构建产物
  reload         刷新项目依赖
  clean          清理项目构建产物
  cache          管理 Conan 包缓存
  install        安装 Package（无参数时安装内置 packages）
  publish        发布 Package（打包到本地缓存）
  toolchain      管理编译工具链
  config         管理编译配置
        """,
    )

    import sys
    version_info = f"mcli {__version__} (MCLang CLI)\nPython: {sys.executable}"
    parser.add_argument(
        "--version",
        action="version",
        version=version_info,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # build 命令
    build_parser = subparsers.add_parser(
        "build",
        help="构建项目",
    )
    build_parser.add_argument(
        "-bt",
        "--build-type",
        type=str,
        choices=["debug", "release"],
        default="debug",
        dest="bt",
        help="构建类型 (debug/release, 默认: debug)",
    )
    build_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="详细输出",
    )
    build_parser.add_argument(
        "--system-compiler",
        action="store_true",
        dest="system_compiler",
        help="使用系统编译器而不是 mclang 内置工具链",
    )
    build_parser.add_argument(
        "--target",
        type=str,
        help="交叉编译目标平台 (如 linux-x86_64)",
    )
    build_parser.add_argument(
        "-tc",
        "--toolchain",
        type=str,
        help="指定工具链名称（默认使用默认工具链）",
    )
    build_parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        dest="parallel_jobs",
        help="Number of parallel build jobs (default: auto-detect, 30%% of CPU cores)",
    )
    build_parser.add_argument(
        "-o",
        "--option",
        action="append",
        dest="conan_options",
        metavar="KEY=VALUE",
        help="Pass options to conan recipe (e.g., -o nuitka_standalone=False, -o create_wheel=True). Use package/*:option for dependencies.",
    )
    build_parser.set_defaults(func=cmd_build)

    # install 命令
    install_parser = subparsers.add_parser(
        "install",
        help="安装 Package（无参数时安装内置 packages）",
    )
    install_parser.add_argument(
        "packages",
        nargs="*",
        help="Package 名称（如 mcl_runtime-darwin-arm64-0.1.0）",
    )
    install_parser.add_argument(
        "--from",
        dest="from_archive",
        help="从本地压缩包安装",
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖已存在的 packages",
    )
    install_parser.add_argument(
        "--list",
        action="store_true",
        dest="list_packages",
        help="列出已安装的 packages",
    )
    install_parser.set_defaults(func=cmd_install)

    # reload 命令
    reload_deps_parser = subparsers.add_parser(
        "reload",
        help="刷新项目依赖",
    )
    reload_deps_parser.add_argument(
        "-bt",
        "--build-type",
        type=str,
        choices=["debug", "release"],
        default="debug",
        dest="bt",
        help="依赖构建类型 (debug/release, 默认: debug)",
    )
    reload_deps_parser.add_argument(
        "-tc",
        "--toolchain",
        type=str,
        default=None,
        help="工具链名称 (默认使用默认工具链)",
    )
    reload_deps_parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="目标平台 (如 darwin-arm64, linux-x86_64，默认使用主机平台)",
    )
    reload_deps_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="详细输出",
    )
    reload_deps_parser.set_defaults(func=cmd_reload_deps)

    # publish 命令
    from .commands.publish import setup_parser as setup_publish_parser
    publish_parser = setup_publish_parser(subparsers)
    publish_parser.set_defaults(func=cmd_publish)

    # test 命令
    test_parser = subparsers.add_parser(
        "test",
        help="运行项目测试",
    )
    test_parser.add_argument(
        "test_names",
        nargs="*",
        help="测试名称（用于 CTest -R 筛选，如 mcc_gtests）",
    )
    test_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="详细输出",
    )
    test_parser.add_argument(
        "-bt",
        "--build-type",
        type=str,
        choices=["debug", "release"],
        default="debug",
        dest="bt",
        help="依赖构建类型 (debug/release, 默认: debug)",
    )
    test_parser.add_argument(
        "--system-compiler",
        action="store_true",
        dest="system_compiler",
        help="使用系统编译器而不是 mclang 内置工具链",
    )
    test_parser.add_argument(
        "--target",
        type=str,
        help="交叉编译目标平台 (如 linux-x86_64)",
    )
    test_parser.add_argument(
        "-tc",
        "--toolchain",
        type=str,
        help="指定工具链名称（默认使用默认工具链）",
    )
    test_parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        dest="parallel_jobs",
        help="Number of parallel build jobs (default: auto-detect, 30%% of CPU cores)",
    )
    test_parser.add_argument(
        "-o",
        "--option",
        action="append",
        dest="conan_options",
        metavar="KEY=VALUE",
        help="Pass options to conan recipe (e.g., -o test=True). Use package/*:option for dependencies.",
    )
    test_parser.set_defaults(func=cmd_test)

    # run 命令
    run_parser = subparsers.add_parser(
        "run",
        help="运行项目构建产物",
    )
    run_parser.add_argument(
        "-bt",
        "--build-type",
        dest="bt",
        choices=["debug", "release"],
        default=None,
        help="构建类型 (debug/release)，未指定时使用现有构建配置或默认值",
    )
    run_parser.add_argument(
        "--target",
        help="指定要运行的目标名称",
    )
    run_parser.add_argument(
        "args",
        nargs="*",
        help="传递给可执行文件的参数",
    )
    run_parser.set_defaults(func=cmd_run)

    # toolchain 命令
    from .commands.toolchain import setup_parser as setup_toolchain_parser

    toolchain_parser = setup_toolchain_parser(subparsers)
    toolchain_parser.set_defaults(func=cmd_toolchain)

    # config 命令（git config 风格）
    config_parser = subparsers.add_parser(
        "config",
        help="管理编译配置（类似 git config）",
    )
    config_parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="显示所有生效配置",
    )
    config_parser.add_argument(
        "--get",
        metavar="KEY",
        help="获取配置值",
    )
    config_parser.add_argument(
        "--set",
        nargs=2,
        metavar=("KEY", "VALUE"),
        help="设置配置值",
    )
    config_parser.add_argument(
        "--unset",
        metavar="KEY",
        help="删除配置值",
    )
    config_parser.add_argument(
        "--global",
        action="store_true",
        dest="global_scope",
        help="操作用户全局配置 (~/.mclang/config.toml)",
    )
    config_parser.add_argument(
        "--local",
        action="store_true",
        help="操作项目配置 (mds/service.json)",
    )
    config_parser.add_argument(
        "--target",
        help="指定目标平台",
    )
    config_parser.set_defaults(func=cmd_config)

    # create 命令
    from .commands.create import setup_parser as setup_create_parser

    create_parser = setup_create_parser(subparsers)
    create_parser.set_defaults(func=cmd_create)

    # setup 命令
    from .commands.setup import setup_parser as setup_setup_parser

    setup_parser = setup_setup_parser(subparsers)
    setup_parser.set_defaults(func=cmd_setup)

    # clean 命令
    from .commands.clean import setup_parser as setup_clean_parser

    clean_parser = setup_clean_parser(subparsers)
    clean_parser.set_defaults(func=cmd_clean)

    # cache 命令
    from .commands.cache import setup_parser as setup_cache_parser

    cache_parser = setup_cache_parser(subparsers)
    cache_parser.set_defaults(func=cmd_cache)

    # 对于 test 和 run 命令，先从命令行中提取 -- 分隔符
    # 这样 -- 之后的参数能绕过 argparse 的参数识别
    sys_argv = sys.argv[1:]
    test_separator_idx = -1
    if len(sys_argv) > 0 and sys_argv[0] in ("test", "run"):
        try:
            test_separator_idx = sys_argv.index("--")
        except ValueError:
            pass

    if test_separator_idx >= 0:
        # 使用 parse_known_args() 只解析 -- 之前的参数
        args, unknown = parser.parse_known_args(sys_argv[:test_separator_idx])
        # -- 之后的参数全部作为未知参数转发
        framework_args = sys_argv[test_separator_idx + 1:]
        unknown = framework_args + unknown
    else:
        # 没有 -- 分隔符，正常解析
        args, unknown = parser.parse_known_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # 对于 test 和 run 命令，允许转发未知参数
    if args.command in ("test", "run"):
        args.unknown_args = unknown
    elif unknown:
        # 其他命令不接受未知参数
        parser.error(f"unrecognized arguments: {' '.join(unknown)}")

    try:
        result = args.func(args)
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(130)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
