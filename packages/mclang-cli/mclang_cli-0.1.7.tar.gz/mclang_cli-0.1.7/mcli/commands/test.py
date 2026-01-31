# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# openUBMC is licensed under Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

"""
mcli test 命令 - 运行 MCLang 项目测试
"""

from pathlib import Path


def _get_project_dir() -> Path:
    return Path.cwd()


def run_test(args) -> bool:
    from ..config import ProjectConfig
    from ..logging import get_logger

    verbose = getattr(args, "verbose", False)

    # 初始化 logger (在 try 块之前)
    logger = get_logger("test", Path.cwd(), "debug")

    try:
        project_dir = _get_project_dir()
        logger.info(f"[DEBUG test.py] Path.cwd()={Path.cwd()}")
        logger.info(f"[DEBUG test.py] project_dir={project_dir}")
    except RuntimeError as e:
        logger.error(str(e))
        return False

    # 读取项目配置
    config_obj = ProjectConfig(project_dir)
    if not config_obj.service_json_path.exists():
        logger.error(f"未找到 {config_obj.service_json_path}，请在 MCLang 项目目录中运行此命令")
        return False

    try:
        project_config = config_obj.load()
    except Exception as e:
        logger.error(f"无法解析 service.json: {e}")
        return False

    # 解析构建参数
    build_type = args.bt.capitalize()
    toolchain_name = getattr(args, "toolchain", None)
    target = getattr(args, "target", None)

    # 确定工具链和目标
    from ..toolchain import get_host_target
    from ..toolchain.manager import get_toolchain_manager

    logger = get_logger("test", project_dir, build_type.lower())

    host_target = get_host_target()
    if target is None:
        target = host_target

    tm = get_toolchain_manager()
    if toolchain_name:
        toolchain = tm.get_toolchain(toolchain_name)
        if not toolchain:
            logger.error(f"工具链 '{toolchain_name}' 不存在")
            return False
    else:
        # 使用默认工具链
        toolchain = tm.get_default()
        if not toolchain:
            logger.error("未配置工具链")
            return False

    # 构建并测试（for_test=True 启用 test 选项）
    from .build import run_build_conan
    import os

    # 设置测试筛选环境变量
    test_names = getattr(args, "test_names", None)
    if test_names:
        # 如果提供了多个测试名，用 | 连接作为正则表达式（CTest -R 支持正则）
        filter_pattern = "|".join(test_names)
        os.environ["MCLI_TEST_FILTER"] = filter_pattern
    if verbose:
        os.environ["MCLI_TEST_VERBOSE"] = "1"

    # 转发未知参数给测试框架
    unknown_args = getattr(args, "unknown_args", [])
    if unknown_args:
        os.environ["MCLI_TEST_ARGS"] = " ".join(unknown_args)

    if verbose:
        logger.info("构建并测试项目...")

    if not run_build_conan(args, project_dir, toolchain_name, build_type, for_test=True):
        logger.error("构建或测试失败")
        return False

    if verbose:
        logger.info("✓ 构建完成，测试已运行")

    return True
