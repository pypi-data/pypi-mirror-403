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
MCLang 项目配置读取模块

支持 service.json 格式（兼容 bingo CI 流程）
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class ProjectConfig:
    """项目配置类"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.service_json_path = project_dir / "mds" / "service.json"
        self._config = None

    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self._config is not None:
            return self._config

        if not self.service_json_path.exists():
            raise FileNotFoundError(
                f"未找到配置文件: {self.service_json_path}\n"
                f"请确保在 MCLang 项目目录中运行此命令"
            )

        with open(self.service_json_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

        return self._config

    @property
    def config(self) -> Dict[str, Any]:
        """获取配置"""
        if self._config is None:
            self.load()
        return self._config

    @property
    def name(self) -> str:
        """获取项目名称"""
        return self.config.get("name", "unknown")

    @property
    def version(self) -> str:
        """获取项目版本"""
        return self.config.get("version", "0.0.0")

    @property
    def package_type(self) -> str:
        """获取包类型"""
        return self.config.get("type", "library")

    @property
    def description(self) -> str:
        """获取项目描述"""
        return self.config.get("description", "")

    @property
    def mclang_config(self) -> Dict[str, Any]:
        """获取 mclang 特定配置"""
        return self.config.get("mclang", {})

    @property
    def package_config(self) -> Dict[str, Any]:
        """获取包配置"""
        return self.mclang_config.get("package", {})

    @property
    def build_config(self) -> Dict[str, Any]:
        """获取构建配置"""
        return self.mclang_config.get("build", {})

    @property
    def build_options(self) -> Dict[str, Any]:
        """获取构建选项"""
        return self.mclang_config.get("build_options", {})

    @property
    def stubs_config(self) -> Dict[str, Any]:
        """获取 stubs 配置"""
        return self.mclang_config.get("stubs", {})

    @property
    def dependencies(self) -> Dict[str, Any]:
        """获取依赖配置"""
        return self.config.get("dependencies", {})

    @property
    def test_dependencies(self) -> list:
        """获取测试依赖"""
        deps = self.dependencies.get("test", [])
        return deps

    @property
    def build_dependencies(self) -> list:
        """获取构建依赖"""
        deps = self.dependencies.get("build", [])
        return deps

    def get_conan_dependencies(self, dep_type: str = "test") -> list:
        """
        获取 Conan 依赖

        Args:
            dep_type: 依赖类型 ("test" 或 "build")

        Returns:
            依赖列表
        """
        deps = self.dependencies.get(dep_type, [])
        conan_deps = []
        for dep in deps:
            if "conan" in dep:
                conan_deps.append(dep["conan"])
        return conan_deps


def load_project_config(project_dir: Optional[Path] = None) -> ProjectConfig:
    """
    加载项目配置

    Args:
        project_dir: 项目目录，默认为当前工作目录

    Returns:
        ProjectConfig 对象
    """
    if project_dir is None:
        project_dir = Path.cwd()

    return ProjectConfig(project_dir)
