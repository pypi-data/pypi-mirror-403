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
MCLI 日志工具

提供分级日志功能：
- 全量日志输出到日志文件（build/.mclang/logs/）
- 控制台显示关键日志行（过滤后的原始输出）
- 警告和错误始终显示在控制台

使用方式：
    from mcli.logging import get_logger, print_summary
    logger = get_logger("build")
    print_summary("构建配置: toolchain=zig")  # 始终显示
    logger.info("原始日志行")  # 控制台过滤，文件完整
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List


class ConsoleFilter(logging.Filter):
    """控制台过滤器 - 过滤噪音，保留重要信息"""

    def __init__(self):
        super().__init__()
        # 过滤噪音（黑名单）- 这些行不显示在控制台
        self.noise_patterns = [
            r'^=+$',  # 分隔线
            r'^--------+',  # 分隔线
            r'^========',  # Conan section 分隔线
            r'^WARN: legacy:',  # Conan legacy 警告
            r'^Use \'&:toolchain=',  # Conan toolchain 提示
            r'^Use \'\*:toolchain=',  # Conan toolchain 提示
            r'Shell cwd was reset',  # Shell 重置信息
            r'^\s*$',  # 空行
            # Profile 详细配置（包含缩进变化）
            r'^\[settings\]$',
            r'^\s{0,4}arch=',
            r'^\s{0,4}build_type=',
            r'^\s{0,4}compiler=',
            r'^\s{0,4}compiler\.',
            r'^\s{0,4}os=',
            r'^\[options\]$',
            r'^\s{0,4}toolchain=',
            r'^\[conf\]$',
            r'^\s{0,4}tools\.build:',
            r'^\[buildenv\]$',
            r'^\s{0,4}CC=',
            r'^\s{0,4}CXX=',
            # CMake 检测信息
            r'^-- The C compiler',
            r'^-- The CXX compiler',
            r'^-- Detecting C compiler',
            r'^-- Detecting CXX compiler',
            # Conan toolchain 详情
            r'^-- Conan toolchain: Defining',
            r'^-- Conan: Component target',
            r'^-- Conan: Target declared',
            # CMakeLists.txt 提示
            r'^\s{0,4}find_package\(',
            r'^\s{0,4}target_link_libraries\(',
            r'^\s{0,4}\(cmake>=',
            r'^\s{0,4}\(cmake<',
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志消息

        规则：
        1. ERROR/WARNING 始终显示
        2. 包含 warning/error 的行始终显示
        3. 过滤噪音模式
        4. 其他 INFO 日志都显示
        """
        message = record.getMessage()

        import re

        # ERROR 和 WARNING 始终显示
        if record.levelno >= logging.WARNING:
            return True

        # 包含 warning 或 error 的行始终显示（编译器警告等）
        if re.search(r'warning:|error:', message, re.IGNORECASE):
            return True

        # 过滤噪音
        for pattern in self.noise_patterns:
            if re.search(pattern, message):
                return False

        # 其他 INFO 日志都显示
        return record.levelno >= logging.INFO


class MCLFormatter(logging.Formatter):
    """MCLang 专用日志格式化器"""

    # 控制台格式（简洁，带时间戳）
    CONSOLE_FORMAT = "%(asctime)s %(message)s"

    # 文件格式（详细，带时间戳）
    FILE_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s"

    # 时间戳格式（HH:MM:SS）
    DATE_FORMAT = "%H:%M:%S"


_loggers = {}


def get_logger(name: str, project_dir: Optional[Path] = None, build_type: str = "debug") -> logging.Logger:
    """获取或创建日志记录器

    Args:
        name: 日志记录器名称（如 "build", "run", "publish"）
        project_dir: 项目目录（保留参数以兼容，暂不使用）
        build_type: 构建类型（保留参数以兼容，暂不使用）

    Returns:
        配置好的日志记录器
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(f"mcli.{name}")
    logger.setLevel(logging.DEBUG)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = MCLFormatter(
        MCLFormatter.CONSOLE_FORMAT,
        datefmt=MCLFormatter.DATE_FORMAT
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(ConsoleFilter())
    logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger


def configure_logging(verbosity: int = 0, quiet: bool = False):
    """全局配置日志级别

    Args:
        verbosity: 详细级别（0=正常，1=详细，2=非常详细）
        quiet: 安静模式（只输出错误）
    """
    root_logger = logging.getLogger("mcli")

    if quiet:
        root_logger.setLevel(logging.ERROR)
    elif verbosity == 0:
        root_logger.setLevel(logging.INFO)
    elif verbosity == 1:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.DEBUG)


def print_summary(message: str, logger: Optional[logging.Logger] = None):
    """打印重要摘要信息（始终显示在控制台）

    用于显示关键的构建信息，这些信息应该始终对用户可见。

    Args:
        message: 要显示的消息
        logger: 可选的日志记录器，如果提供则同时记录到日志文件

    Example:
        logger = get_logger("build", project_dir)
        print_summary("构建配置: toolchain=zig, target=darwin-arm64", logger)
    """
    print(message)
    if logger:
        logger.info(message)

