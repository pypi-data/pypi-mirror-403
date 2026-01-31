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
mcli publish 命令 - 发布 Conan Package

使用 Conan 包管理系统发布 MCLang 项目。

功能：
1. 生成 Conan profile（基于当前工具链）
2. 构建项目（确保打包的是正确配置的产物）
3. 执行 conan export-pkg（基于本地构建产物打包）
4. 上传到 Conan 仓库（需指定 -r/--remote）

注意：
- 发布前会先构建项目，确保打包的是最新代码
- 默认只导出到本地缓存，需使用 -r/--remote 才会上传到远端
- --user 和 --channel 必须同时指定，或不指定（Conan2 推荐）
- --channel 的值：如 dev/rc/stable

构建配置优先级（与 mcli run 保持一致）：
1. 如果用户指定了 --bt，使用用户指定的参数
2. 否则读取 .mclang/build-config.json 中保存的最后一次构建配置
3. 如果没有现有构建，使用默认参数 (bt=debug)
"""

import subprocess
from pathlib import Path
from typing import Optional


def run_publish_conan(args, project_dir: Path, toolchain_name: Optional[str]) -> bool:
    """使用 Conan 发布 Package

    Args:
        args: 命题行参数
        project_dir: 项目目录
        toolchain_name: 工具链名称

    Returns:
        是否成功
    """
    from mcli.toolchain.manager import get_toolchain_manager
    from mcli.toolchain import get_host_target
    from mcli.config import load_project_config
    from mcli.logging import get_logger
    from .run import load_build_config, BuildConfig

    # 初始化 logger
    logger = get_logger("publish", project_dir, "debug")

    # 加载 service.json
    config = load_project_config(project_dir)
    pkg_name = config.name
    pkg_version = str(config.version)  # 确保是字符串

    # 获取构建配置（与 mcli run 保持一致）
    user_specified_channel = getattr(args, "channel", None)
    user_specified_bt = getattr(args, "bt", None)

    # Conan 2 推荐不使用 user/channel，如果要使用必须同时指定
    conan_user = getattr(args, "user", None)
    conan_channel = None

    # 验证 user/channel 参数组合
    if user_specified_channel is not None and conan_user is None:
        logger.error("错误：指定了 --channel 但未指定 --user")
        logger.info("  Conan 2 中 user/channel 必须同时指定，或不使用")
        logger.info("  示例 1（推荐）: mcli publish")
        logger.info("  示例 2（传统格式）: mcli publish --user xxx --channel dev")
        return False

    if conan_user is not None and user_specified_channel is None:
        logger.error("错误：指定了 --user 但未指定 --channel")
        logger.info("  Conan 2 中 user/channel 必须同时指定，或不使用")
        logger.info("  示例 1（推荐）: mcli publish")
        logger.info("  示例 2（传统格式）: mcli publish --user xxx --channel dev")
        return False

    # 如果指定了 user，使用指定的 channel
    if conan_user is not None:
        conan_channel = user_specified_channel or "dev"

    if user_specified_bt:
        # 用户指定了 build_type
        build_type = user_specified_bt
        build_config = BuildConfig(build_type=build_type)
    else:
        # 用户未指定参数，尝试加载上次构建配置
        saved_config = load_build_config(project_dir)
        if saved_config:
            build_config = saved_config
            build_type = build_config.build_type
        else:
            # 没有保存的配置，使用默认值
            build_config = BuildConfig(build_type="debug")
            build_type = build_config.build_type

    requested_bt = build_type.capitalize()  # Debug or Release

    logger.info(f"发布 {pkg_name} v{pkg_version} (Conan)...")
    if conan_user:
        logger.info(f"  User: {conan_user}")
        logger.info(f"  Channel: {conan_channel}")
    else:
        logger.info("  User/Channel: 未指定")
    logger.info(f"  构建类型: {requested_bt}")

    # 获取工具链信息
    tm = get_toolchain_manager()
    if toolchain_name:
        toolchain = tm.get_toolchain(toolchain_name)
        if not toolchain:
            logger.error(f"工具链 '{toolchain_name}' 不存在")
            return False
    else:
        toolchain = tm.get_default()

    # 获取目标平台和 C++ 标准
    if toolchain:
        manifest = toolchain.manifest
        if manifest:
            target = manifest.host
        else:
            target = get_host_target()

        config = toolchain.get_config()
        compiler_config = config.get("compiler", {})
        cpp_std = compiler_config.get("cpp_std", "c++17")

        logger.info(f"    目标: {target}")
        logger.info(f"    编译器: {toolchain.compiler_type} {toolchain.compiler_version}")
        logger.info(f"    C++ 标准: {cpp_std}")
    else:
        logger.warning("未找到工具链")
        target = get_host_target()

    # 生成 Conan profile
    logger.info("  生成 Conan profile...")
    try:
        from mcli.toolchain.conan_profile import generate_conan_profile
        profile_path = generate_conan_profile(
            toolchain_name=toolchain.name if toolchain else "default",
            toolchain_path=toolchain._toolchain_dir if toolchain else Path.cwd(),
            target=target,
            build_type=requested_bt,
            project_dir=project_dir,
        )
        logger.debug(f"    Profile: {profile_path}")
    except Exception as e:
        logger.warning(f"生成 Conan profile 失败: {e}")

    # 先构建项目，确保打包的是正确配置的产物
    # conanbase.py 将由 build.py 中的 _ensure_conanbase_in_project 统一生成
    logger.info("  构建项目...")
    from .build import run_build_conan

    if not run_build_conan(args, project_dir, toolchain_name, requested_bt):
        logger.error("构建失败，无法发布")
        return False

    # 执行 conan export-pkg（基于本地构建产物打包）
    logger.info("  打包 Conan 包...")
    conan_export_cmd = [
        "conan", "export-pkg", ".",
        "--name", pkg_name,
        "--version", pkg_version,
    ]

    # 只有在用户明确指定时才添加 user/channel
    if conan_user:
        conan_export_cmd.extend(["--user", conan_user])
        if conan_channel:
            conan_export_cmd.extend(["--channel", conan_channel])

    conan_export_cmd.extend([
        "-pr:h", str(profile_path) if toolchain else "default",
        "-pr:b", str(profile_path) if toolchain else "default",
    ])

    result = subprocess.run(conan_export_cmd, cwd=project_dir)
    if result.returncode != 0:
        logger.error("conan export-pkg 失败")
        return False

    logger.info("✓ Conan 包已导出到本地缓存")

    # 上传到远端仓库（需要显式指定 -r/--remote）
    remote = getattr(args, "remote", None)
    if not remote:
        logger.info("未指定远端仓库，跳过上传（使用 -r/--remote 指定远端仓库）")
        return True

    # 根据是否指定 user/channel 生成不同的包引用
    if conan_user:
        pkg_ref = f"{pkg_name}/{pkg_version}@{conan_user}/{conan_channel}"
        logger.info(f"上传到远端仓库 {remote} ({conan_user}/{conan_channel})...")
    else:
        pkg_ref = f"{pkg_name}/{pkg_version}"
        logger.info(f"上传到远端仓库 {remote}...")

    # 构建上传命令
    conan_upload_cmd = ["conan", "upload", pkg_ref, "-r", remote]

    # 如果用户指定了 --force，强制覆盖远端已存在的包
    force_upload = getattr(args, "force", False)
    if force_upload:
        conan_upload_cmd.append("--force")
        logger.info("  强制覆盖模式 (--force)")

    result = subprocess.run(conan_upload_cmd, cwd=project_dir)
    if result.returncode != 0:
        logger.warning("conan upload 失败（包可能已存在或仓库未配置）")
        return True  # 不视为失败，本地包已可用

    if conan_user:
        logger.info(f"✓ 上传成功 (channel: {conan_channel})")
    else:
        logger.info("✓ 上传成功")
    return True


def run_publish(args) -> bool:
    """发布 Package"""
    from mcli.config import load_project_config
    from mcli.logging import get_logger

    project_dir = Path.cwd()
    logger = get_logger("publish", project_dir, "debug")

    # 加载 service.json
    try:
        config = load_project_config(project_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        return False

    pkg_name = config.name
    pkg_version = config.version

    # 检测构建系统：只支持 Conan
    conanfile = project_dir / "conanfile.py"

    if not conanfile.exists():
        logger.error("mcli publish 现在只支持 Conan 构建系统")
        logger.info("请确保项目目录中存在 conanfile.py 文件。")
        logger.info("如需创建新的 Conan 项目，请使用 mcli create。")
        return False

    toolchain_name = getattr(args, "toolchain", None)

    # 使用 Conan 发布
    logger.info("检测到 conanfile.py，使用 Conan 发布")
    return run_publish_conan(args, project_dir, toolchain_name)


def setup_parser(subparsers):
    """配置 publish 命令的参数解析器"""
    import argparse
    publish_parser = subparsers.add_parser(
        "publish",
        help="发布 MCLang 包",
        description="发布 MCLang 包到 Conan 仓库",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    publish_parser.add_argument(
        "--channel",
        type=str,
        default=None,
        help="Conan channel (需与 --user 同时指定)",
    )

    publish_parser.add_argument(
        "-bt",
        "--build-type",
        dest="bt",
        type=str,
        default="debug",
        choices=["debug", "release"],
        help="构建类型 (debug/release，默认: debug)",
    )

    publish_parser.add_argument(
        "-r", "--remote",
        type=str,
        default=None,
        help="上传到指定的远端仓库（不指定则不上传）",
    )

    publish_parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖远端已存在的包",
    )

    publish_parser.add_argument(
        "-tc",
        "--toolchain",
        type=str,
        default=None,
        help="指定工具链（默认使用默认工具链）",
    )

    publish_parser.add_argument(
        "--user",
        type=str,
        default=None,
        help="Conan 包所有者",
    )

    return publish_parser
