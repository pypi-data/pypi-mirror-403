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
Conan Package 工具函数
提供与 Conan 包管理系统的集成功能：
1. 使用 conan graph info 命令获取 Conan 实际选择的包
2. 获取包的 stubs 配置
3. 构建完整的包引用用于获取包路径
"""


import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class PackageReference:
    """Conan 包引用

    包含获取包路径所需的完整信息：
    - name/version@user/channel#recipe_rev:package_id#package_rev
    """
    name: str
    version: str
    user: str = ""
    channel: str = ""
    recipe_rev: str = ""
    package_id: str = ""
    package_rev: str = ""

    def to_full_ref(self) -> str:
        """构建完整的 Conan 包引用

        格式: name/version@user/channel#recipe_rev:package_id#package_rev
        """
        parts = [f"{self.name}/{self.version}"]
        if self.user or self.channel:
            parts.append(f"@{self.user}/{self.channel}")
        if self.recipe_rev:
            parts.append(f"#{self.recipe_rev}")
        if self.package_id:
            parts.append(f":{self.package_id}")
        if self.package_rev:
            parts.append(f"#{self.package_rev}")
        return "".join(parts)


def get_project_packages(
    project_dir: Path,
    profile_path: Optional[Path] = None,
    test: bool = False,
    build_type: str = "debug",
) -> List[PackageReference]:
    """获取项目中 Conan 实际选择的包列表

    使用 conan graph info 命令获取当前项目配置下 Conan 选择的包。
    这与 Conan 的包选择逻辑完全一致。

    Args:
        project_dir: 项目目录
        profile_path: Conan profile 路径（如果未提供，将尝试从项目查找）
        test: 是否为测试模式（会添加 -o *:test=True 选项）

    Returns:
        PackageReference 列表
    """
    # 如果未提供 profile，尝试从项目目录查找
    if not profile_path:
        profile_path = _find_project_profile(project_dir, build_type)
        if not profile_path:
            return []

    # 构建 conan graph info 命令
    cmd = [
        "conan", "graph", "info", ".",
        "--format=json",
        "-pr:h", str(profile_path),
        "-pr:b", str(profile_path),
    ]
    if test:
        cmd.extend(["-o", "&:test=True"])

    try:
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []

        data = json.loads(result.stdout)
        packages = []

        # 解析 conan graph info 输出
        graph = data.get("graph", {})
        nodes = graph.get("nodes", {})

        for node_id, node in nodes.items():
            # 跳过根节点（项目自身）
            if node.get("recipe") == "Consumer":
                continue

            # 跳过没有 package_id 的节点（未解析的包）
            if not node.get("package_id"):
                continue

            ref_str = node.get("ref", "")
            if not ref_str:
                continue

            # 解析引用
            pkg_ref = _parse_graph_node(ref_str, node)
            if pkg_ref:
                packages.append(pkg_ref)

        return packages

    except (json.JSONDecodeError, Exception):
        return []


def get_package_path(pkg_ref: PackageReference) -> Optional[Path]:
    """获取包的安装路径

    Args:
        pkg_ref: 包引用

    Returns:
        包的 p/ 目录路径，如果未找到返回 None
    """
    try:
        from conan.api.model.refs import PkgReference
        from conan.api.conan_api import ConanAPI

        api = ConanAPI()
        full_ref = pkg_ref.to_full_ref()

        # 使用 PkgReference.loads 解析完整引用
        # 注意：完整引用必须包含 package_id 和 package_rev
        pref = PkgReference.loads(full_ref)

        # 获取包路径
        pkg_path = Path(api.cache.package_path(pref))
        if pkg_path.exists():
            return pkg_path

    except Exception:
        pass

    return None


def _find_project_profile(project_dir: Path, build_type: str = "debug") -> Optional[Path]:
    """查找项目级 Conan profile

    Args:
        project_dir: 项目目录
        build_type: 构建类型 (debug/release)

    Returns:
        Profile 路径，如果未找到返回 None
    """
    profiles_dir = project_dir / ".mclang" / "conan" / "profiles"
    if not profiles_dir.exists():
        return None

    # 优先查找匹配 build_type 的 profile
    build_type_lower = build_type.lower()
    for profile_file in profiles_dir.iterdir():
        if build_type_lower in profile_file.name.lower():
            return profile_file

    # 回退到第一个可用的 profile
    for profile_file in profiles_dir.iterdir():
        if profile_file.is_file():
            return profile_file

    return None


def _parse_graph_node(ref_str: str, node: Dict[str, Any]) -> Optional[PackageReference]:
    """解析 conan graph info 的节点

    Args:
        ref_str: 引用字符串（如 "mclruntime/0.1.2@openubmc/dev#recipe_rev"）
        node: 图节点数据

    Returns:
        PackageReference 对象
    """
    # 解析 ref 字符串
    # 格式: name/version@user/channel#recipe_rev
    name = node.get("name", "")
    version = node.get("version", "")
    user = node.get("user", "") or ""
    channel = node.get("channel", "") or ""
    recipe_rev = node.get("rrev", "") or ""

    # 获取 package_id 和 package_rev
    package_id = node.get("package_id", "")
    package_rev = node.get("prev", "") or ""

    if not name or not version:
        return None

    return PackageReference(
        name=name,
        version=version,
        user=user,
        channel=channel,
        recipe_rev=recipe_rev,
        package_id=package_id,
        package_rev=package_rev,
    )


def get_package_stubs_dir(package_path: Path) -> Optional[Path]:
    """获取包的 stubs 目录

    Args:
        package_path: 包的 p/ 目录路径

    Returns:
        stubs 目录路径，如果不存在返回 None
    """
    stubs_dir = package_path / "stubs"
    if stubs_dir.exists() and stubs_dir.is_dir():
        return stubs_dir
    return None


def get_package_stubs_config(package_path: Path) -> Optional[Dict[str, Any]]:
    """获取包的 stubs 配置

    Args:
        package_path: 包的 p/ 目录路径

    Returns:
        stubs 配置字典，如果不存在返回 None

    Note:
        尝试从多个路径读取配置（按优先级）：
        1. include/mds/service.json（bingo 打包路径）
        2. mds/service.json（包根目录路径）
        配置格式：{"mclang": {"stubs": {...}}}
    """
    # 尝试多个路径查找 service.json
    service_json_paths = [
        package_path / "include" / "mds" / "service.json",  # bingo 打包路径
        package_path / "mds" / "service.json",              # 包根目录路径
    ]

    for service_json in service_json_paths:
        if service_json.exists():
            try:
                with open(service_json, "r") as f:
                    pkg_info = json.load(f)
                stubs_config = pkg_info.get("mclang", {}).get("stubs")
                if stubs_config:
                    return stubs_config
            except (json.JSONDecodeError, IOError):
                continue

    return None


def list_stub_packages(package_path: Path) -> List[str]:
    """列出包中可用的 stub 包

    Args:
        package_path: 包的 p/ 目录路径

    Returns:
        stub 包名列表
    """
    stubs_config = get_package_stubs_config(package_path)
    if stubs_config:
        return stubs_config.get("packages", [])

    # 回退：扫描 stubs 目录
    stubs_dir = get_package_stubs_dir(package_path)
    if not stubs_dir:
        return []

    stub_packages = []
    for item in stubs_dir.iterdir():
        if item.is_dir() and (item / "__init__.py").exists():
            stub_packages.append(item.name)

    return stub_packages
