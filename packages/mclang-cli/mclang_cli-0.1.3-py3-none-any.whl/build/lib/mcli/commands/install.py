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
mcli install 命令 - 安装 MCLang Package

功能：
1. 从本地 .tar.gz 文件安装 Package
2. 从远程下载并安装（待实现）
3. ABI 兼容性检查
4. 安装 Python stub 文件到 ~/.mclang/packages/
5. 安装 C++ 二进制文件和头文件
6. 更新项目 mclang.toml 依赖（可选）

注意：
- 当前版本仅支持本地安装（--from 参数）
- 远程下载功能需要 mclang-index 集成，后续实现
- 隐式源码构建功能后续实现

Copyright (c) 2026 Huawei Technologies Co., Ltd.
openUBMC is licensed under Mulan PSL v2.
"""

import json
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import List, Optional

from ...package import PackageManager
from ...package.abi import (
    ABICompatibility,
    ABIInfo,
    check_abi_compatibility,
    parse_package_name,
)
from ..paths import get_packages_dir


def install_stub_files(
    package_dir: Path,
    package_name: str,
    stub_dir: Path,
) -> bool:
    """安装 stub 文件到 ~/.mclang/packages/{package_name}/

    Args:
        package_dir: 包安装目录（包含 mclang.json 和 stubs/）
        package_name: 包名称（如 mcl_runtime）
        stub_dir: stub 文件目标目录（如 ~/.mclang/packages/mcl_runtime/）

    Returns:
        是否成功
    """
    # 读取 mclang.json
    mclang_json_path = package_dir / "mclang.json"
    if not mclang_json_path.exists():
        return False

    try:
        with open(mclang_json_path, "r") as f:
            mclang_json = json.load(f)
    except (json.JSONDecodeError, IOError):
        return False

    stubs_config = mclang_json.get("stubs", {})
    if not stubs_config:
        return False

    stub_dir.mkdir(parents=True, exist_ok=True)

    # stubs 目录在包目录中
    stubs_source = package_dir / "stubs"
    if not stubs_source.exists():
        return False

    # 复制所有 stub 文件
    stub_count = 0
    for stub_pkg in stubs_config.get("packages", []):
        stub_pkg_source = stubs_source / stub_pkg
        if stub_pkg_source.exists() and stub_pkg_source.is_dir():
            dest_dir = stub_dir / stub_pkg
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(stub_pkg_source, dest_dir)
            stub_count += len(list(dest_dir.rglob("*.py")))

    print(f"  ✓ Stub 文件已安装 ({stub_count} 个文件) → {stub_dir}")
    return True


def install_binaries(
    extract_dir: Path,
    target_dir: Path,
) -> bool:
    """安装 C++ 二进制文件和头文件

    Args:
        extract_dir: 解压后的目录
        target_dir: 目标安装目录

    Returns:
        是否成功
    """
    # 读取 mclang.json
    mclang_json_path = extract_dir / "mclang.json"
    if not mclang_json_path.exists():
        print("  警告: 未找到 mclang.json")
        return False

    try:
        with open(mclang_json_path, "r") as f:
            mclang_json = json.load(f)
    except (json.JSONDecodeError, IOError):
        print("  警告: 无法读取 mclang.json")
        return False

    cpp_info = mclang_json.get("cpp", {})
    libraries = cpp_info.get("libraries", [])
    headers = cpp_info.get("headers", [])

    if not libraries and not headers:
        print("  警告: 包中没有 C++ 文件")
        return False

    target_dir.mkdir(parents=True, exist_ok=True)

    # 复制库文件
    lib_count = 0
    for lib_path in libraries:
        src_file = extract_dir / lib_path
        if src_file.exists():
            dest_file = target_dir / lib_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            lib_count += 1

    # 复制头文件
    header_count = 0
    for header_item in headers:
        # header_item 可能是:
        # 1. dict: {"source": "build"/"source", "path": "include/mc"}
        # 2. str: "include/mc" (兼容旧格式)
        if isinstance(header_item, dict):
            header_path = header_item.get("path", "")
        else:
            header_path = str(header_item)

        # 头文件在包内统一在 include/ 目录下
        src_dir = extract_dir / "include"
        if src_dir.exists() and src_dir.is_dir():
            # 复制整个 include 目录
            dest_dir = target_dir / "include"
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(src_dir, dest_dir)
            header_count += 1
            break  # 只需复制一次

    print(f"  ✓ C++ 文件已安装: {lib_count} 个库, {header_count} 个头文件目录 → {target_dir}")
    return True


def check_abi_from_package(extract_dir: Path) -> tuple:
    """检查包的 ABI 兼容性

    Args:
        extract_dir: 解压后的目录

    Returns:
        (ABICompatibility, 消息列表)
    """
    # 读取 mclang.json
    mclang_json_path = extract_dir / "mclang.json"
    if not mclang_json_path.exists():
        return ABICompatibility.INCOMPATIBLE, ["错误: 未找到 mclang.json"]

    try:
        with open(mclang_json_path, "r") as f:
            mclang_json = json.load(f)
    except (json.JSONDecodeError, IOError):
        return ABICompatibility.INCOMPATIBLE, ["错误: 无法读取 mclang.json"]

    # 获取包的 ABI 信息
    abi_data = mclang_json.get("abi")
    if not abi_data:
        return ABICompatibility.INCOMPATIBLE, ["错误: 包中没有 ABI 信息"]

    package_abi = ABIInfo.from_dict(abi_data)

    # 获取当前 ABI
    try:
        current_abi = ABIInfo.from_system()
    except Exception as e:
        return ABICompatibility.INCOMPATIBLE, [f"错误: 无法获取当前 ABI: {e}"]

    # 检查兼容性
    return check_abi_compatibility(package_abi, current_abi)


def install_from_archive(archive_path: Path, force: bool = False) -> bool:
    """从本地 .tar.gz 文件安装包

    Args:
        archive_path: 压缩包路径
        force: 是否强制安装（跳过 ABI 检查）

    Returns:
        是否成功
    """
    if not archive_path.exists():
        print(f"错误: 压缩包不存在: {archive_path}")
        return False

    # 解析包名
    filename = archive_path.name
    if filename.endswith(".tar.gz"):
        package_full_name = filename[:-7]
    else:
        print(f"错误: 不支持的压缩包格式: {filename}")
        return False

    parsed = parse_package_name(package_full_name)
    if not parsed:
        print(f"错误: 无法解析包名: {package_full_name}")
        print("包名格式应为: {{name}}-{{target}}-{{compiler}}-{{version}}.tar.gz")
        return False

    package_name = parsed["name"]
    pkg_type = parsed.get("name", package_name)

    print(f"安装 {package_full_name}...")

    # 检查是否已安装
    manager = PackageManager()
    if manager.is_installed(package_full_name) and not force:
        print(f"✓ {package_full_name} 已安装")
        return True

    # 解压到临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        print("  解压中...")
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                # 安全检查
                for member in tar.getmembers():
                    if member.name.startswith("/") or ".." in member.name:
                        print(f"错误: 不安全的压缩包: {member.name}")
                        return False
                tar.extractall(tmpdir)
        except tarfile.TarError as e:
            print(f"错误: 解压失败: {e}")
            return False

        # 找到解压后的目录
        extracted = list(tmpdir.iterdir())
        if len(extracted) == 1 and extracted[0].is_dir():
            extract_dir = extracted[0]
        else:
            extract_dir = tmpdir

        # ABI 兼容性检查
        if not force:
            print("  检查 ABI 兼容性...")
            compatibility, messages = check_abi_from_package(extract_dir)

            if compatibility == ABICompatibility.INCOMPATIBLE:
                print(f"  ✗ ABI 不兼容:")
                for msg in messages:
                    print(f"    {msg}")
                print(f"\n  解决方案:")
                print(f"    1. 使用与包相同的工具链")
                print(f"    2. 使用 --force 强制安装（可能导致运行时错误）")
                print(f"    3. 从源码构建（功能待实现）")
                return False
            elif compatibility == ABICompatibility.WARNING:
                print(f"  ⚠ ABI 警告:")
                for msg in messages:
                    print(f"    {msg}")

        # 确定最终安装位置（所有包统一安装到 packages 目录）
        final_dir = manager._packages_dir / package_full_name
        final_dir.parent.mkdir(parents=True, exist_ok=True)

        # 如果已存在，先删除
        if final_dir.exists():
            shutil.rmtree(final_dir)

        # 移动到最终位置
        shutil.move(str(extract_dir), str(final_dir))
        print(f"  ✓ 包已安装到: {final_dir}")

        # 安装 stub 文件（用于 IDE 支持和 mcc 编译器）
        stub_dir = manager._packages_dir / package_name
        if not install_stub_files(final_dir, package_name, stub_dir):
            print("  提示: 此包没有 stub 文件")

    print(f"\n✓ {package_full_name} 安装完成")
    return True


def run_install(args) -> bool:
    """安装 Package"""
    packages = args.packages if args.packages else []

    if args.from_archive:
        # 从本地文件安装
        return install_from_archive(Path(args.from_archive), force=args.force)

    if not packages:
        # 从 mclang.toml 读取依赖
        mclang_toml = Path.cwd() / "mclang.toml"
        if mclang_toml.exists():
            print("从 mclang.toml 安装依赖...")
            # TODO: 解析 mclang.toml 获取依赖列表
            print("提示: 依赖解析功能待实现")
            return True
        else:
            print("错误: 请指定要安装的 Package 或在项目目录中运行")
            print("\n用法:")
            print("  mcli install --from <package.tar.gz>   # 从本地文件安装")
            print("  mcli install <package-name>            # 从远程安装（待实现）")
            return False

    # 从远程安装（待实现）
    print("从远程安装功能待实现")
    print("提示: 当前仅支持本地安装，使用 --from 参数")
    return False


def setup_parser(subparsers):
    """设置 install 命令的参数解析器"""
    parser = subparsers.add_parser(
        "install",
        help="安装 MCLang Package",
        formatter_class=lambda prog: None,
    )

    parser.add_argument(
        "packages",
        nargs="*",
        help="包名称（远程安装功能待实现）",
    )

    parser.add_argument(
        "--from",
        dest="from_archive",
        type=str,
        help="从本地 .tar.gz 文件安装",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="强制安装，跳过 ABI 检查",
    )

    return parser
