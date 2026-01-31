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
工具链管理器
管理多个工具链实例，支持：
- 列出所有工具链
- 添加/删除工具链
- 获取默认工具链
- 根据名称获取工具链
"""


from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from .toolchain import Toolchain, ToolchainManifest
from ..paths import get_mclang_home


class ToolchainError(Exception):
    """工具链错误"""
    pass


@dataclass
class ToolchainInfo:
    """工具链信息（用于列表显示）"""
    name: str
    compiler_type: str
    compiler_version: str
    is_default: bool = False


class ToolchainManager:
    """工具链管理器

    管理多个工具链实例。

    目录结构：
        ~/.mclang/toolchains/
        ├── clang/
        │   ├── manifest.toml
        │   └── config.toml
        ├── zig/
        │   ├── manifest.toml
        │   └── config.toml
        └── default  # 符号链接，指向默认工具链
    """

    def __init__(self, mclang_home: Optional[Path] = None):
        if mclang_home is None:
            mclang_home = get_mclang_home()

        self._home = mclang_home
        self._toolchains_dir = mclang_home / "toolchains"
        self._default_link = self._toolchains_dir / "default"

    def list_toolchains(self) -> List[ToolchainInfo]:
        """列出所有工具链"""
        toolchains = []

        if not self._toolchains_dir.exists():
            return []

        # 获取默认工具链名称
        default_name = self.get_default_name()

        for item in self._toolchains_dir.iterdir():
            if item.is_dir() and item.name != "default":
                manifest_path = item / "manifest.toml"
                if manifest_path.exists():
                    manifest = ToolchainManifest.from_file(manifest_path)
                    if manifest:
                        toolchains.append(
                            ToolchainInfo(
                                name=item.name,
                                compiler_type=manifest.compiler_type,
                                compiler_version=manifest.compiler_version,
                                is_default=(item.name == default_name),
                            )
                        )

        return toolchains

    def get_toolchain(self, name: str) -> Optional[Toolchain]:
        """获取指定名称的工具链"""
        toolchain_dir = self._toolchains_dir / name
        if not toolchain_dir.exists():
            return None

        return Toolchain.from_directory(name, toolchain_dir, self._home)

    def get_default(self) -> Optional[Toolchain]:
        """获取默认工具链"""
        default_name = self.get_default_name()
        if default_name:
            return self.get_toolchain(default_name)

        # 如果没有设置默认，尝试返回第一个可用的
        toolchains = self.list_toolchains()
        if toolchains:
            return self.get_toolchain(toolchains[0].name)

        return None

    def get_default_name(self) -> Optional[str]:
        """获取默认工具链名称"""
        if not self._default_link.exists():
            return None

        try:
            # 读取符号链接
            target = self._default_link.readlink()
            return target.name
        except (OSError, AttributeError):
            # 尝试读取文件内容（非符号链接方式）
            try:
                return self._default_link.read_text().strip()
            except Exception:
                return None

    def add_toolchain(
        self,
        name: str,
        compiler_type: str,
        compiler_path: Optional[Path] = None,
        set_as_default: bool = False,
        force: bool = False,
    ) -> Toolchain:
        """添加工具链

        Args:
            name: 工具链名称
            compiler_type: 编译器类型 (zig, gcc, clang)
            compiler_path: 编译器路径（可选）
            set_as_default: 是否设为默认
            force: 是否覆盖已存在的工具链

        Returns:
            Toolchain 实例

        Raises:
            ToolchainError: 工具链已存在且未指定 force
        """
        # 检查是否是第一个工具链
        is_first = len(self.list_toolchains()) == 0

        # 检查是否已存在
        toolchain_dir = self._toolchains_dir / name
        if toolchain_dir.exists() and not force:
            # 检查是否是同一个工具链
            existing = self.get_toolchain(name)
            if existing:
                raise ToolchainError(
                    f"工具链 '{name}' 已存在\n"
                    f"  编译器: {existing.compiler_type} {existing.compiler_version}\n"
                    f"  使用 --force 覆盖，或使用 --name 指定不同的名称"
                )

        # 创建工具链
        toolchain = Toolchain.create(
            name=name,
            compiler_type=compiler_type,
            compiler_path=compiler_path,
            mclang_home=self._home,
        )

        # 设置为默认（第一个工具链自动设为默认）
        if is_first or set_as_default:
            self.set_default(name)

        return toolchain

    def remove_toolchain(self, name: str) -> bool:
        """删除工具链"""
        toolchain = self.get_toolchain(name)
        if not toolchain:
            return False

        # 如果是默认工具链，清除默认设置
        if name == self.get_default_name():
            self._clear_default()

        return toolchain.remove()

    def set_default(self, name: str) -> bool:
        """设置默认工具链"""
        toolchain = self.get_toolchain(name)
        if not toolchain:
            return False

        self._toolchains_dir.mkdir(parents=True, exist_ok=True)

        # 删除旧的符号链接
        if self._default_link.exists():
            self._default_link.unlink()

        # 创建新的符号链接
        try:
            self._default_link.symlink_to(toolchain._toolchain_dir)
        except OSError:
            # 如果符号链接失败，使用文件方式
            self._default_link.write_text(name)

        return True

    def _clear_default(self) -> None:
        """清除默认工具链设置"""
        if self._default_link.exists():
            try:
                self._default_link.unlink()
            except Exception:
                pass

    def toolchain_exists(self, name: str) -> bool:
        """检查工具链是否存在"""
        toolchain_dir = self._toolchains_dir / name
        return toolchain_dir.exists() and (toolchain_dir / "manifest.toml").exists()


# 全局单例
_manager: Optional[ToolchainManager] = None


def get_toolchain_manager() -> ToolchainManager:
    """获取工具链管理器单例"""
    global _manager
    if _manager is None:
        _manager = ToolchainManager()
    return _manager


# 向后兼容函数（用于旧 API）
def get_default_toolchain():
    """获取默认工具链（向后兼容）

    注意：返回新的 Toolchain 实例，不是旧的 Toolchain 类
    """
    manager = get_toolchain_manager()
    return manager.get_default()
