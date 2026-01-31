# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# openUBMC is licensed under Mulan PSL v2.
# You can obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

"""
mcli clean 命令 - 清理项目构建产物

清理构建目录、缓存、依赖等。
"""

import shutil
from pathlib import Path
from typing import Optional

from ..config import load_project_config
from ..logging import get_logger
from ..paths import get_build_folder_name, get_build_dir


def run_clean(args) -> bool:
    """执行清理操作"""
    project_dir = Path.cwd()
    logger = get_logger("clean", project_dir, "debug")

    # 检查是否在项目目录
    try:
        config = load_project_config(project_dir)
    except FileNotFoundError:
        logger.error("未找到项目配置文件（mds/service.json 或 mclang.toml）")
        logger.info("提示: 请在 MCLang 项目目录中运行此命令")
        return False

    # 解析参数
    verbose = getattr(args, "verbose", False)

    # 清理构建目录
    build_folder_name = get_build_folder_name(project_dir)
    build_dir = project_dir / build_folder_name

    if not build_dir.exists():
        if verbose:
            logger.info("构建目录不存在，无需清理")
        return True

    # 统计要删除的文件
    file_count = sum(1 for _ in build_dir.rglob("*") if _.is_file())
    dir_count = sum(1 for _ in build_dir.rglob("*") if _.is_dir())

    if verbose:
        logger.info(f"清理构建目录: {build_folder_name}/")
        logger.info(f"  文件: {file_count}")
        logger.info(f"  目录: {dir_count}")

    try:
        shutil.rmtree(build_dir)
        if not verbose:
            logger.info(f"✓ 已清理构建目录 ({file_count} 文件, {dir_count} 目录)")
    except OSError as e:
        logger.error(f"清理构建目录失败: {e}")
        return False

    return True


def setup_parser(subparsers):
    """设置 clean 命令的参数解析器"""
    clean_parser = subparsers.add_parser(
        "clean",
        help="清理项目构建产物",
        description="清理 MCLang 项目的构建目录",
    )

    clean_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="显示详细输出",
    )

    return clean_parser
