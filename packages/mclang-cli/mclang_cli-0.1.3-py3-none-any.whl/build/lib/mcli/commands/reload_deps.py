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
mcli reload-deps 命令
功能：
1. 使用 conan graph info 检查 Conan 会选择哪些包
2. 刷新 .mclang/packages/ 中的 stub 软链接
使用场景：
- 项目 B 依赖项目 A（版本约束 >=）
- 项目 A 发布了新版本，变更了 stub API
- 项目 B 需要先运行 reload-deps 更新 stub，再修复代码，最后构建
"""


from pathlib import Path
from argparse import Namespace
from ..package.deps import sync_mclang_dir


def run_reload_deps(args: Namespace) -> bool:
    """执行 reload-deps 命令

    Args:
        args: 命令行参数
            - verbose: 详细输出

    Returns:
        是否成功
    """
    from ..logging import get_logger

    project_dir = Path.cwd()
    logger = get_logger("reload", project_dir, "debug")

    # 检查是否在项目目录
    service_path = project_dir / "mds/service.json"
    if not service_path.exists():
        logger.error("未找到 mds/service.json，请在 MCLang 项目目录中运行此命令")
        return False

    verbose = getattr(args, "verbose", False)

    logger.info("检查 Conan 包选择...")
    if verbose:
        logger.debug(f"  项目目录: {project_dir}")

    # 同步 .mclang/ 目录（内部使用 conan graph info）
    changed = sync_mclang_dir(project_dir, dep_type="test", verbose=verbose)

    if changed:
        logger.info("✓ Stub 链接已更新")
    else:
        logger.info("✓ Stub 链接已是最新")

    logger.info("提示: IDE 现在应该可以看到最新的类型信息")
    return True
