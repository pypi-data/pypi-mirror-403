# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# openUBMC is licensed under Mulan PSL v2.
# You can obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

"""
mcli cache 命令

管理 Conan 包缓存

子命令:
- mcli cache ls: 列出所有缓存的包
- mcli cache search <pattern>: 搜索包（支持通配符 *）
- mcli cache remove <target>: 删除指定的包（支持通配符和预览模式）
- mcli cache clean: 清除所有 Conan 包缓存
"""

import argparse
import fnmatch
import shutil
from pathlib import Path


def run_cache(args) -> bool:
    """cache 命令主入口"""
    subcommand = getattr(args, "cache_command", None)

    if subcommand == "ls":
        return cmd_ls(args)
    elif subcommand == "search":
        return cmd_search(args)
    elif subcommand == "remove":
        return cmd_remove(args)
    elif subcommand == "clean":
        return cmd_clean(args)
    else:
        print("用法: mcli cache <command>")
        print("")
        print("可用命令:")
        print("  ls                列出所有缓存的包")
        print("  search <pattern>  搜索包（支持通配符 *）")
        print("  remove <target>   删除指定的包（支持通配符）")
        print("  clean             清除所有 Conan 包缓存")
        print("")
        print("remove 命令目标格式:")
        print("  package_name              删除指定包名的所有版本")
        print("  package_name/version      删除指定包的特定版本")
        print("  package_name/version:hash 删除特定的包实例")
        print("  hash                      通过包 hash 删除特定实例")
        print("")
        print("示例:")
        print("  mcli cache remove mclruntime")
        print("  mcli cache remove mclruntime/0.1.7")
        print("  mcli cache remove mclruntime/0.1.7:c62f50179333")
        print("  mcli cache remove c62f50179333")
        print("  mcli cache remove mcl* --preview  # 预览将要删除的包")
        return True


def cmd_ls(args) -> bool:
    """列出所有缓存的包"""
    import json
    import subprocess

    verbose = getattr(args, "verbose", False)

    # 使用 conan list 命令获取包信息
    try:
        result = subprocess.run(
            ["conan", "list", "*:*", "--format=json"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            print(f"无法获取包信息: {result.stderr}")
            return False
        data = json.loads(result.stdout)
    except Exception as e:
        print(f"解析包信息失败: {e}")
        return False

    # 计算总缓存大小
    total_cache_size = _get_cache_total_size()

    # 解析本地缓存数据
    local_cache = data.get("Local Cache", {})

    if not local_cache:
        print("没有缓存的包")
        return True

    # 按包名组织数据
    packages_by_name = {}

    for ref, ref_data in local_cache.items():
        # ref 格式: "mclruntime/0.1.7"
        if "/" not in ref:
            continue

        parts = ref.split("/", 1)
        pkg_name = parts[0]
        version = parts[1] if len(parts) > 1 else ""

        if pkg_name not in packages_by_name:
            packages_by_name[pkg_name] = {}

        if version not in packages_by_name[pkg_name]:
            packages_by_name[pkg_name][version] = []

        # 获取该版本的所有包实例
        for rev_data in ref_data.get("revisions", {}).values():
            for pkg_id, pkg_data in rev_data.get("packages", {}).items():
                info = pkg_data.get("info", {})
                settings = info.get("settings", {})

                build_type = settings.get("build_type", "Unknown")
                compiler = f"{settings.get('compiler', 'unknown')}-{settings.get('compiler.version', '?')}"

                packages_by_name[pkg_name][version].append({
                    "id": pkg_id[:12],  # 缩短显示
                    "build_type": build_type,
                    "compiler": compiler,
                })

    # 显示结果
    if verbose:
        # 详细模式：显示所有包实例
        for pkg_name in sorted(packages_by_name.keys()):
            print(f"{pkg_name}:")
            for version in sorted(packages_by_name[pkg_name].keys(), reverse=True):
                packages = packages_by_name[pkg_name][version]
                print(f"  {version} ({len(packages)} 个包实例):")
                for pkg in packages:
                    print(f"    {pkg['id']}  {pkg['compiler']:10}  {pkg['build_type']:8}")
    else:
        # 简洁模式：按包名→版本显示
        for pkg_name in sorted(packages_by_name.keys()):
            versions = list(packages_by_name[pkg_name].keys())
            versions_str = ", ".join(sorted(versions, reverse=True))
            total_pkgs = sum(len(pkgs) for pkgs in packages_by_name[pkg_name].values())
            print(f"  {pkg_name:30} {versions_str:20} ({total_pkgs} 个包实例)")

    print("")
    print(f"缓存总大小: {_format_size(total_cache_size)}")

    return True


def _get_cache_total_size() -> int:
    """计算缓存总大小"""
    total_size = 0
    base_dir = Path.home() / ".conan2" / "p"

    if not base_dir.exists():
        return 0

    try:
        total_size = sum(f.stat().st_size for f in base_dir.rglob("*") if f.is_file())
    except Exception:
        pass

    return total_size


def _format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def cmd_remove(args) -> bool:
    """删除指定的包"""
    import subprocess
    import fnmatch

    target = getattr(args, "target", None)
    force = getattr(args, "force", False)
    preview = getattr(args, "preview", False)

    if not target:
        print("错误: 请提供要删除的目标")
        print("")
        print("用法: mcli cache remove <target> [options]")
        print("")
        print("目标格式:")
        print("  package_name              删除指定包名的所有版本")
        print("  package_name/version      删除指定包的特定版本")
        print("  package_name/version:hash 删除特定的包实例")
        print("  hash                      通过包 hash 删除特定实例")
        print("")
        print("示例:")
        print("  mcli cache remove mclruntime")
        print("  mcli cache remove mclruntime/0.1.7")
        print("  mcli cache remove mclruntime/0.1.7:c62f50179333")
        print("  mcli cache remove c62f50179333")
        print("  mcli cache remove mcl* --preview  # 预览将要删除的包")
        return False

    # 检查是否是通配符模式
    has_wildcard = "*" in target or "?" in target

    # 如果是通配符模式，使用批量删除
    if has_wildcard:
        return _remove_by_wildcard(target, force, preview)

    # 解析目标并构建 conan remove pattern
    # 格式: package_name, package_name/version, package_name/version:hash, 或 hash
    if ":" in target:
        # package_name/version:hash 或 hash 格式
        if "/" in target:
            # package_name/version:hash
            parts = target.split(":")
            if len(parts) == 2:
                ref, pkg_hash = parts
                # 使用通配符匹配 hash 前缀: mclruntime/0.1.7:*47877e0a*
                conan_pattern = f"{ref}:*{pkg_hash}*"
            else:
                conan_pattern = target
        else:
            # 只有 hash，需要查找完整的引用
            conan_pattern = _find_ref_by_hash(target)
            if not conan_pattern:
                print(f"错误: 未找到 hash 为 '{target}' 的包")
                print("")
                print("提示: 使用 'mcli cache ls -v' 查看所有包实例及其 hash")
                return False
    elif "/" in target:
        # package_name/version 或 package_name/version:hash
        conan_pattern = target
    else:
        # 只有 package_name
        conan_pattern = target

    # 预览模式或确认前显示将要删除的内容
    matched_packages = _list_matching_packages(conan_pattern)

    if not matched_packages:
        print(f"警告: 未找到匹配 '{conan_pattern}' 的包")
        print("")
        print("提示: 使用 'mcli cache ls' 查看所有缓存的包")
        return True

    # 显示预览信息
    _print_removal_preview(matched_packages, conan_pattern)

    # 预览模式只显示不删除
    if preview:
        print("")
        print("预览模式: 使用 --force 或移除 --preview 选项来实际删除")
        return True

    # 确认操作
    if not force:
        response = input("确认删除? (yes/no): ")
        if response.lower() not in ("yes", "y"):
            print("操作已取消")
            return True

    # 使用 conan remove 命令删除
    try:
        result = subprocess.run(
            ["conan", "remove", conan_pattern, "-c"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            # 解析错误信息，提供更友好的提示
            stderr = result.stderr.strip()
            if "ERROR" in stderr or "error" in stderr.lower():
                print(f"错误: 删除失败")
                print(f"详情: {stderr}")
            else:
                print(f"错误: {stderr}")
            return False

        # 显示删除结果
        if matched_packages:
            total_count = matched_packages["total_count"]
            print(f"✓ 成功删除 {total_count} 个包")
        return True
    except FileNotFoundError:
        print("错误: 未找到 conan 命令")
        print("请确保已安装 Conan 2.x")
        return False
    except Exception as e:
        print(f"错误: 删除失败 - {e}")
        return False


def _find_ref_by_hash(pkg_hash: str) -> str:
    """通过 hash 查找完整的包引用

    返回完整的 conan pattern，如: package_name/version:*hash_prefix*
    如果找到多个匹配，返回第一个
    """
    import json
    import subprocess

    try:
        result = subprocess.run(
            ["conan", "list", "*:*", "--format=json"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        local_cache = data.get("Local Cache", {})
        lower_hash = pkg_hash.lower()

        # 遍历所有包查找匹配的 hash
        for ref, ref_data in local_cache.items():
            revisions = ref_data.get("revisions", {})
            for rev_hash, rev_data in revisions.items():
                packages = rev_data.get("packages", {})
                for pkg_id in packages.keys():
                    # 检查完整匹配或前缀匹配
                    if pkg_id.lower() == lower_hash or pkg_id.lower().startswith(lower_hash):
                        # 返回格式: package_name/version:*hash*
                        # 使用完整的 hash 前缀匹配
                        return f"{ref}:{pkg_id}"

        return None
    except Exception:
        return None


def _list_matching_packages(pattern: str) -> dict:
    """列出匹配给定 pattern 的所有包

    返回包含匹配包信息的字典:
    {
        "packages": {"pkg_name/version": {"instances": [...]},
        "total_count": int,
        "total_size": int
    }
    """
    import json
    import subprocess
    import fnmatch

    try:
        result = subprocess.run(
            ["conan", "list", "*:*", "--format=json"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        local_cache = data.get("Local Cache", {})

        matched = {"packages": {}, "total_count": 0, "total_size": 0}
        has_wildcard = "*" in pattern or "?" in pattern

        for ref, ref_data in local_cache.items():
            # 检查是否匹配 pattern
            if not _is_pattern_match(ref, pattern, has_wildcard):
                continue

            matched["packages"][ref] = {"instances": []}

            # 统计该引用下的所有包实例
            for rev_data in ref_data.get("revisions", {}).values():
                for pkg_id, pkg_data in rev_data.get("packages", {}).items():
                    info = pkg_data.get("info", {})
                    settings = info.get("settings", {})

                    build_type = settings.get("build_type", "Unknown")
                    compiler = f"{settings.get('compiler', 'unknown')}-{settings.get('compiler.version', '?')}"

                    matched["packages"][ref]["instances"].append({
                        "id": pkg_id,
                        "id_short": pkg_id[:12],
                        "build_type": build_type,
                        "compiler": compiler,
                    })
                    matched["total_count"] += 1

        return matched if matched["packages"] else None
    except Exception:
        return None


def _is_pattern_match(ref: str, pattern: str, has_wildcard: bool) -> bool:
    """检查引用是否匹配 pattern

    Args:
        ref: 包引用，如 "mclruntime/0.1.7"
        pattern: 匹配模式，如 "mclruntime", "mclruntime/*", "mcl*"
        has_wildcard: 是否包含通配符

    Returns:
        是否匹配
    """
    if has_wildcard:
        # 通配符匹配
        if "/" in pattern:
            # 完整 pattern 匹配
            return fnmatch.fnmatch(ref, pattern)
        else:
            # 只匹配包名部分
            pkg_name = ref.split("/")[0]
            return fnmatch.fnmatch(pkg_name, pattern)
    else:
        # 精确前缀匹配
        if pattern.endswith(":"):
            # pattern like "mclruntime/0.1.7:" - 匹配该版本的所有包实例
            return ref.startswith(pattern)
        elif pattern.endswith("/"):
            # pattern like "mclruntime/" - 匹配该包的所有版本
            return ref.startswith(pattern)
        else:
            # 精确匹配 ref 或前缀匹配
            return ref == pattern or ref.startswith(pattern + "/")


def _print_removal_preview(matched_packages: dict, pattern: str) -> None:
    """打印删除预览信息"""
    print(f"匹配 '{pattern}' 的包:")
    print("")

    for ref, ref_data in matched_packages["packages"].items():
        instances = ref_data["instances"]
        print(f"  {ref} ({len(instances)} 个包实例):")
        for inst in instances:
            print(f"    {inst['id_short']}  {inst['compiler']:10}  {inst['build_type']:8}")

    print("")
    total_count = matched_packages["total_count"]
    print(f"总计: {total_count} 个包实例将被删除")


def _remove_by_wildcard(pattern: str, force: bool, preview: bool) -> bool:
    """使用通配符模式删除包"""
    import subprocess

    # 列出匹配的包
    matched = _list_matching_packages(pattern)

    if not matched:
        print(f"警告: 未找到匹配 '{pattern}' 的包")
        print("")
        print("提示: 使用 'mcli cache ls' 查看所有缓存的包")
        return True

    # 显示预览信息
    _print_removal_preview(matched, pattern)

    # 预览模式只显示不删除
    if preview:
        print("")
        print("预览模式: 使用 --force 或移除 --preview 选项来实际删除")
        return True

    # 确认操作
    if not force:
        response = input("确认删除? (yes/no): ")
        if response.lower() not in ("yes", "y"):
            print("操作已取消")
            return True

    # 对每个匹配的引用执行删除
    success_count = 0
    failed_patterns = []

    for ref in matched["packages"].keys():
        try:
            result = subprocess.run(
                ["conan", "remove", ref, "-c"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                success_count += 1
            else:
                failed_patterns.append(ref)
        except Exception:
            failed_patterns.append(ref)

    # 显示结果
    if success_count > 0:
        print(f"✓ 成功删除 {success_count} 个引用的包")

    if failed_patterns:
        print(f"警告: 以下引用删除失败:")
        for ref in failed_patterns:
            print(f"  - {ref}")
        return False

    return True


def cmd_search(args) -> bool:
    """搜索缓存的包"""
    import json
    import subprocess
    import fnmatch

    pattern = getattr(args, "pattern", None)
    verbose = getattr(args, "verbose", False)

    if not pattern:
        print("请提供搜索模式")
        return False

    # 使用 conan list 命令获取包信息
    try:
        result = subprocess.run(
            ["conan", "list", "*:*", "--format=json"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            print(f"无法获取包信息: {result.stderr}")
            return False
        data = json.loads(result.stdout)
    except Exception as e:
        print(f"解析包信息失败: {e}")
        return False

    # 解析本地缓存数据
    local_cache = data.get("Local Cache", {})

    if not local_cache:
        print("没有缓存的包")
        return True

    # 按包名组织数据，同时过滤匹配的包
    packages_by_name = {}

    # 确定匹配模式
    has_wildcard = "*" in pattern or "?" in pattern
    if "/" in pattern:
        # 包含斜杠，作为前缀匹配
        prefix = pattern
        search_term = None
    elif has_wildcard:
        # 包含通配符，使用通配符匹配
        prefix = None
        search_term = None
    else:
        # 纯文本，子串匹配
        prefix = None
        search_term = pattern.lower()

    for ref, ref_data in local_cache.items():
        # ref 格式: "mclruntime/0.1.7"
        if "/" not in ref:
            continue

        parts = ref.split("/", 1)
        pkg_name = parts[0]
        version = parts[1] if len(parts) > 1 else ""

        # 匹配逻辑
        matched = False
        if prefix is not None:
            # 前缀匹配
            matched = ref.startswith(prefix)
        elif search_term is not None:
            # 子串匹配
            matched = (search_term in pkg_name.lower() or search_term in ref.lower())
        else:
            # 通配符匹配
            matched = fnmatch.fnmatch(pkg_name, pattern) or fnmatch.fnmatch(ref, pattern)

        if not matched:
            continue

        if pkg_name not in packages_by_name:
            packages_by_name[pkg_name] = {}

        if version not in packages_by_name[pkg_name]:
            packages_by_name[pkg_name][version] = []

        # 获取该版本的所有包实例
        for rev_data in ref_data.get("revisions", {}).values():
            for pkg_id, pkg_data in rev_data.get("packages", {}).items():
                info = pkg_data.get("info", {})
                settings = info.get("settings", {})

                build_type = settings.get("build_type", "Unknown")
                compiler = f"{settings.get('compiler', 'unknown')}-{settings.get('compiler.version', '?')}"

                packages_by_name[pkg_name][version].append({
                    "id": pkg_id[:12],
                    "build_type": build_type,
                    "compiler": compiler,
                })

    if not packages_by_name:
        print(f"没有找到匹配 '{pattern}' 的包")
        return True

    # 显示结果
    if verbose:
        # 详细模式
        for pkg_name in sorted(packages_by_name.keys()):
            print(f"{pkg_name}:")
            for version in sorted(packages_by_name[pkg_name].keys(), reverse=True):
                packages = packages_by_name[pkg_name][version]
                print(f"  {version} ({len(packages)} 个包实例):")
                for pkg in packages:
                    print(f"    {pkg['id']}  {pkg['compiler']:10}  {pkg['build_type']:8}")
    else:
        # 简洁模式
        for pkg_name in sorted(packages_by_name.keys()):
            versions = list(packages_by_name[pkg_name].keys())
            versions_str = ", ".join(sorted(versions, reverse=True))
            total_pkgs = sum(len(pkgs) for pkgs in packages_by_name[pkg_name].values())
            print(f"  {pkg_name:30} {versions_str:20} ({total_pkgs} 个包实例)")

    print("")
    print(f"找到 {len(packages_by_name)} 个匹配的包")

    return True


def cmd_clean(args) -> bool:
    """清除所有 Conan 包缓存"""
    conan_cache_dir = Path.home() / ".conan2" / "p"

    if not conan_cache_dir.exists():
        print("Conan 缓存目录不存在，无需清理")
        return True

    # 确认操作
    force = getattr(args, "force", False)
    if not force:
        print(f"将删除目录: {conan_cache_dir}")
        print("⚠️  这将清除所有项目的 Conan 包缓存，不仅仅是当前项目")
        print("")
        response = input("确认删除? (yes/no): ")
        if response.lower() not in ("yes", "y"):
            print("操作已取消")
            return True

    try:
        shutil.rmtree(conan_cache_dir)
        print(f"✓ 已清除 Conan 包缓存: {conan_cache_dir}")
    except OSError as e:
        print(f"错误: 清除缓存失败: {e}")
        return False

    return True


def setup_parser(subparsers) -> argparse.ArgumentParser:
    """设置 cache 子命令解析器"""
    parser = subparsers.add_parser(
        "cache",
        help="管理 Conan 包缓存",
    )

    cache_subparsers = parser.add_subparsers(
        dest="cache_command",
        help="缓存命令",
    )

    # ls 命令
    ls_parser = cache_subparsers.add_parser(
        "ls",
        help="列出所有缓存的包",
    )
    ls_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="显示详细信息",
    )

    # list 命令（别名）
    list_parser = cache_subparsers.add_parser(
        "list",
        help="列出所有缓存的包（别名）",
    )
    list_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="显示详细信息",
    )

    # search 命令
    search_parser = cache_subparsers.add_parser(
        "search",
        help="搜索缓存的包",
    )
    search_parser.add_argument(
        "pattern",
        help="搜索模式（支持通配符 *，如 mcl* 或 mclruntime/*）",
    )
    search_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="显示详细信息",
    )

    # remove 命令
    remove_parser = cache_subparsers.add_parser(
        "remove",
        help="删除指定的包",
    )
    remove_parser.add_argument(
        "target",
        help="要删除的目标（支持通配符，如 mcl*、mclruntime/0.1.7、mclruntime/0.1.7:c62f50179333 或 c62f50179333）",
    )
    remove_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="跳过确认提示",
    )
    remove_parser.add_argument(
        "-p",
        "--preview",
        action="store_true",
        help="预览将要删除的包，但不实际删除",
    )

    # clean 命令
    clean_parser = cache_subparsers.add_parser(
        "clean",
        help="清除所有 Conan 包缓存",
    )
    clean_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="跳过确认提示",
    )

    return parser
