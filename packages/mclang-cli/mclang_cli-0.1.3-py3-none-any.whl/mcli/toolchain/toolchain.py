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
工具链类
表示单个工具链实例，包含：
- 编译器类型和版本
- 工具链配置（从模板生成）
- 支持的目标平台（基于已安装的 mcl_runtime）
"""


from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import re
from mcli.template import ProjectTemplate
from .base import (
    COMPILER_ZIG,
    COMPILER_GCC,
    COMPILER_CLANG,
    get_host_target,
)


@dataclass
class ToolchainManifest:
    """工具链清单"""
    version: str  # 工具链配置版本
    host: str  # 宿主平台
    compiler_type: str  # 编译器类型：zig, gcc, clang
    compiler_version: str  # 编译器版本
    compiler_path: Optional[str] = None  # 编译器路径（用于本地工具链）

    @classmethod
    def from_file(cls, path: Path) -> Optional["ToolchainManifest"]:
        """从 manifest.toml 加载"""
        import tomllib

        if not path.exists():
            return None

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)

            toolchain = data.get("toolchain", {})
            compiler = data.get("compiler", {})

            return cls(
                version=toolchain.get("version", "unknown"),
                host=toolchain.get("host", "unknown"),
                compiler_type=compiler.get("type", COMPILER_ZIG),
                compiler_version=compiler.get("version", "unknown"),
                compiler_path=compiler.get("path"),
            )
        except Exception:
            return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "host": self.host,
            "compiler_type": self.compiler_type,
            "compiler_version": self.compiler_version,
            "compiler_path": self.compiler_path,
        }


class Toolchain:
    """工具链类

    表示一个已配置的工具链实例。
    """

    def __init__(
        self,
        name: str,
        toolchain_dir: Path,
        mclang_home: Path,
    ):
        self.name = name
        self._toolchain_dir = toolchain_dir
        self._mclang_home = mclang_home

        # 文件路径
        self.manifest_path = toolchain_dir / "manifest.toml"
        self.config_path = toolchain_dir / "config.toml"

    @classmethod
    def create(
        cls,
        name: str,
        compiler_type: str,
        compiler_path: Optional[Path] = None,
        host_target: Optional[str] = None,
        mclang_home: Optional[Path] = None,
    ) -> "Toolchain":
        """创建新工具链

        Args:
            name: 工具链名称
            compiler_type: 编译器类型 (zig, gcc, clang)
            compiler_path: 编译器路径（可选，默认自动检测）
            host_target: 宿主平台（可选，默认自动检测）
            mclang_home: mclang 主目录（可选）

        Returns:
            Toolchain 实例
        """
        from ..paths import get_mclang_home

        if mclang_home is None:
            mclang_home = get_mclang_home()

        if host_target is None:
            host_target = get_host_target()

        # 检测编译器版本和路径
        if compiler_path is None:
            compiler_path = cls._detect_compiler_path(compiler_type)
        else:
            compiler_path = Path(compiler_path)

        if not compiler_path.exists():
            raise ValueError(f"编译器不存在: {compiler_path}")

        compiler_version = cls._get_compiler_version(compiler_type, compiler_path)

        # 检测 macOS 上的 gcc/clang 别名情况
        # 如果 gcc 实际是 Apple Clang，提示用户使用 clang
        if compiler_type == COMPILER_GCC and compiler_version.startswith("apple-clang-"):
            raise ValueError(
                f"检测到 '{compiler_path}' 实际上是 Apple Clang ({compiler_version})\n"
                f"macOS 上的 'gcc' 通常是 Apple Clang 的别名\n"
                f"请使用 '--type clang' 创建 clang 工具链，而不是 gcc"
            )

        # 创建工具链目录
        toolchain_dir = mclang_home / "toolchains" / name
        toolchain_dir.mkdir(parents=True, exist_ok=True)

        # 生成 manifest
        manifest = ToolchainManifest(
            version="1.0",
            host=host_target,
            compiler_type=compiler_type,
            compiler_version=compiler_version,
            compiler_path=str(compiler_path),
        )

        cls._write_manifest(toolchain_dir / "manifest.toml", manifest)

        # 生成配置（从模板）
        cls._generate_config(
            toolchain_dir / "config.toml",
            compiler_type,
            compiler_version,
            host_target,
            str(compiler_path),
        )

        return cls(name, toolchain_dir, mclang_home)

    @staticmethod
    def _detect_compiler_path(compiler_type: str) -> Path:
        """检测编译器路径"""
        import shutil

        if compiler_type == COMPILER_ZIG:
            exe = "zig"
        elif compiler_type == COMPILER_GCC:
            exe = "g++"
        elif compiler_type == COMPILER_CLANG:
            exe = "clang++"
        else:
            raise ValueError(f"未知的编译器类型: {compiler_type}")

        path = shutil.which(exe)
        if not path:
            raise ValueError(f"未找到编译器: {exe}")

        return Path(path)

    @staticmethod
    def _get_compiler_version(compiler_type: str, compiler_path: Path) -> str:
        """获取编译器版本"""
        try:
            if compiler_type == COMPILER_ZIG:
                result = subprocess.run(
                    [str(compiler_path), "version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            else:
                # gcc 和 clang
                result = subprocess.run(
                    [str(compiler_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    first_line = result.stdout.split("\n")[0]

                    # 检测 macOS 上的 gcc/clang 别名情况
                    # macOS 上 "gcc" 通常是 Apple Clang 的别名
                    if "Apple clang" in first_line:
                        # 解析 Apple Clang 版本（如 "Apple clang version 17.0.0"）
                        match = re.search(r"Apple clang version (\d+\.\d+(?:\.\d+)?)", first_line)
                        if match:
                            # 返回 "apple-clang" 前缀的版本，表示这是 Apple Clang
                            return f"apple-clang-{match.group(1)}"

                    # 解析普通版本号
                    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", first_line)
                    if match:
                        return match.group(1)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return "unknown"

    @staticmethod
    def _write_manifest(path: Path, manifest: ToolchainManifest) -> None:
        """写入 manifest.toml"""
        content = f"""# mclang 工具链清单
# 自动生成，请勿手动修改

[toolchain]
version = "{manifest.version}"
host = "{manifest.host}"

[compiler]
type = "{manifest.compiler_type}"
version = "{manifest.compiler_version}"
path = "{manifest.compiler_path or ''}"
"""
        path.write_text(content)

    @staticmethod
    def _platform_to_triple(platform: str) -> str:
        """将 platform 转换为 triple 格式

        Args:
            platform: 平台标识（如 darwin-arm64, linux-x86_64）

        Returns:
            triple 字符串（如 aarch64-macos-none, x86_64-linux-gnu）
        """
        # 解析 platform: os-arch
        parts = platform.split("-")
        if len(parts) >= 2:
            os_name, arch = parts[0], parts[1]
        else:
            # 回退到默认值
            return "x86_64-unknown-linux-gnu"

        # 转换 arch
        arch_map = {
            "x86_64": "x86_64",
            "amd64": "x86_64",
            "arm64": "aarch64",
            "aarch64": "aarch64",
            "i386": "i686",
            "i686": "i686",
        }
        arch_triple = arch_map.get(arch, arch)

        # 转换 os
        if os_name == "darwin":
            os_triple = "macos"
            vendor = "none"
        elif os_name == "linux":
            os_triple = "linux"
            vendor = "gnu"
        elif os_name == "windows":
            os_triple = "windows"
            vendor = "gnu"
        else:
            os_triple = os_name
            vendor = "unknown"

        return f"{arch_triple}-{os_triple}-{vendor}"

    @staticmethod
    def _generate_config(
        path: Path,
        compiler_type: str,
        compiler_version: str,
        platform: str,
        compiler_path: Optional[str] = None,
    ) -> None:
        """从模板生成 config.toml"""
        from ..paths import get_mcli_root

        # 生成 host triple（从 platform 推断）
        host_triple = Toolchain._platform_to_triple(platform)

        # 获取编译器路径和目录
        if compiler_path:
            compiler_dir = str(Path(compiler_path).parent)
        else:
            compiler_dir = ""
            compiler_path = ""

        # 从 platform 解析 target 和 triple
        # platform 格式: darwin-arm64, linux-x86_64, etc.
        if "-" in platform:
            target = platform  # darwin-arm64
        else:
            target = platform

        # 生成 triple（简化版本，用于配置模板）
        triple = host_triple

        # 检查是否有工具链模板
        mcli_root = get_mcli_root()
        toolchain_template_dir = mcli_root / "templates" / "toolchain"

        if toolchain_template_dir.exists():
            template = ProjectTemplate(toolchain_template_dir)

            # 渲染模板
            context = {
                "platform": platform,
                "version": compiler_version,
                "compiler_type": compiler_type,
                "host_triple": host_triple,
                "compiler_path": compiler_path,
                "compiler_dir": compiler_dir,
                "target": target,
                "triple": triple,
            }

            # 渲染配置文件
            config_template = toolchain_template_dir / "config.toml.mct"
            if config_template.exists():
                content = template.render_file(config_template, context)
                path.write_text(content)
                return

        # 默认配置
        content = f"""# mclang 工具链默认配置
# 平台: {platform}
# 编译器: {compiler_type} {compiler_version}

[compiler]
cpp_std = "c++17"

[compiler.args]
common = [
    "-Wall",
    "-Wextra",
]

[compiler.args.debug]
extra = ["-g", "-O0"]
defines = ["DEBUG"]

[compiler.args.release]
extra = ["-O3"]
defines = ["NDEBUG"]

[linker.args]
"""
        if platform.startswith("darwin"):
            content += 'rpath = ["-Wl,-rpath,@loader_path"]\n'
        else:
            content += 'rpath = ["-Wl,-rpath,$ORIGIN"]\n'

        path.write_text(content)

    @classmethod
    def from_directory(cls, name: str, toolchain_dir: Path, mclang_home: Path) -> "Toolchain":
        """从目录加载工具链"""
        return cls(name, toolchain_dir, mclang_home)

    @property
    def manifest(self) -> Optional[ToolchainManifest]:
        """获取工具链清单"""
        return ToolchainManifest.from_file(self.manifest_path)

    @property
    def compiler_type(self) -> str:
        """获取编译器类型"""
        manifest = self.manifest
        return manifest.compiler_type if manifest else COMPILER_ZIG

    @property
    def compiler_version(self) -> str:
        """获取编译器版本"""
        manifest = self.manifest
        return manifest.compiler_version if manifest else "unknown"

    @property
    def compiler_path(self) -> Optional[Path]:
        """获取编译器路径"""
        manifest = self.manifest
        if manifest and manifest.compiler_path:
            return Path(manifest.compiler_path)

        # 尝试从工具链目录获取
        if self.compiler_type == COMPILER_ZIG:
            zig_path = self._toolchain_dir / "zig" / "zig"
            if zig_path.exists():
                return zig_path
        else:
            bin_dir = self._toolchain_dir / "bin"
            if bin_dir.exists():
                if self.compiler_type == COMPILER_GCC:
                    gxx_path = bin_dir / "g++"
                    if gxx_path.exists():
                        return gxx_path
                elif self.compiler_type == COMPILER_CLANG:
                    clangxx_path = bin_dir / "clang++"
                    if clangxx_path.exists():
                        return clangxx_path

        # 自动检测
        try:
            return self._detect_compiler_path(self.compiler_type)
        except ValueError:
            return None

    def get_config(self) -> Dict[str, Any]:
        """获取工具链配置"""
        import tomllib

        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}

    @staticmethod
    def _target_name_to_triple(target: str) -> str:
        """将目标名称转换为 triple

        Args:
            target: 目标名称（如 linux-x86_64, darwin-arm64）

        Returns:
            triple 字符串
        """
        return Toolchain._platform_to_triple(target)

    def remove(self) -> bool:
        """删除工具链"""
        import shutil

        if not self._toolchain_dir.exists():
            return False

        shutil.rmtree(self._toolchain_dir)
        return True

    def exists(self) -> bool:
        """检查工具链是否存在"""
        return self._toolchain_dir.exists() and self.manifest_path.exists()
