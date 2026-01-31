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
MCLang CLI

提供 MCLang 项目的创建、构建、发布和包管理功能。
"""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("mclang-cli")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.1.3"

__author__ = "MCLang Development Team"
__email__ = "mclang@openubmc.com"

# 构建目录配置
BUILD_DIR_NAME = "builddir"  # 构建输出目录名称

from .main import main

__all__ = ["main", "BUILD_DIR_NAME"]
