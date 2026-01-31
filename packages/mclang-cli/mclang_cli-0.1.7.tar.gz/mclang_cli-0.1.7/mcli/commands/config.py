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
mcli config 命令

管理 mclang 编译配置，类似 git config 风格。

配置优先级（从低到高）：
1. 工具链默认配置 (toolchain/config.toml) - 只读
2. 用户全局配置 (~/.mclang/config.toml) - --global
3. 项目配置 (mclang.toml [build]) - --local

用法:
    mcli config --list                          # 显示所有生效配置
    mcli config --get compiler.cpp_std          # 获取配置值
    mcli config --global --set compiler.cpp_std c++20  # 设置全局配置
    mcli config --local --set compiler.args.common "-Wpedantic"  # 设置项目配置

Copyright (c) 2026 Huawei Technologies Co., Ltd.
openUBMC is licensed under Mulan PSL v2.
"""

from pathlib import Path
from typing import Optional, Any

import tomllib


def _load_toml(path: Path) -> dict:
    """加载 TOML 文件"""
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _format_toml_value(value: Any) -> str:
    """格式化 TOML 值"""
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        items = ", ".join(_format_toml_value(v) for v in value)
        return f"[{items}]"
    elif isinstance(value, dict):
        # 嵌套字典需要特殊处理
        return str(value)
    else:
        return f'"{value}"'


def _dict_to_toml_lines(data: dict, prefix: str = "") -> list:
    """递归将字典转换为 TOML 行"""
    lines = []
    tables = []

    for key, value in data.items():
        if isinstance(value, dict) and value:  # 非空字典作为表
            tables.append((key, value))
        elif isinstance(value, dict):  # 空字典跳过
            pass
        else:
            lines.append(f"{key} = {_format_toml_value(value)}")

    # 处理嵌套表
    for table_name, table_data in tables:
        full_name = f"{prefix}.{table_name}" if prefix else table_name

        # 检查是否有直接值（非嵌套字典）
        has_values = any(not isinstance(v, dict) for v in table_data.values())

        if has_values:
            lines.append(f"\n[{full_name}]")
            for key, value in table_data.items():
                if not isinstance(value, dict):
                    lines.append(f"{key} = {_format_toml_value(value)}")

        # 递归处理嵌套字典
        for key, value in table_data.items():
            if isinstance(value, dict) and value:
                nested_lines = _dict_to_toml_lines({key: value}, prefix=full_name)
                lines.extend(nested_lines)

    return lines


def _save_toml(path: Path, data: dict):
    """保存 TOML 文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = _dict_to_toml_lines(data)
    path.write_text("\n".join(lines) + "\n")


def _get_nested(data: dict, key: str) -> Any:
    """获取嵌套字典的值，如 'compiler.cpp_std'"""
    parts = key.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _set_nested(data: dict, key: str, value: Any) -> dict:
    """设置嵌套字典的值"""
    parts = key.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    # 尝试解析值类型
    if value.startswith("[") and value.endswith("]"):
        # 数组
        import json

        try:
            current[parts[-1]] = json.loads(value)
        except json.JSONDecodeError:
            current[parts[-1]] = value
    elif value.lower() in ("true", "false"):
        current[parts[-1]] = value.lower() == "true"
    elif value.isdigit():
        current[parts[-1]] = int(value)
    else:
        current[parts[-1]] = value

    return data


def _unset_nested(data: dict, key: str) -> bool:
    """删除嵌套字典的值"""
    parts = key.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current:
            return False
        current = current[part]

    if parts[-1] in current:
        del current[parts[-1]]
        return True
    return False


def get_config_paths() -> tuple:
    """获取配置文件路径"""
    from ..paths import get_mclang_home
    from ..toolchain import get_host_target
    from ..toolchain.manager import get_toolchain_manager

    mclang_home = get_mclang_home()
    target = get_host_target()

    # 获取默认工具链的配置路径
    tm = get_toolchain_manager()
    default_toolchain = tm.get_default()

    if default_toolchain:
        toolchain_config = default_toolchain.config_path
    else:
        # 回退到旧的单一路径
        toolchain_config = mclang_home / "toolchain" / "config.toml"

    user_config = mclang_home / "config.toml"
    project_config = Path.cwd() / "mclang.toml"

    return toolchain_config, user_config, project_config


def cmd_list(target: Optional[str] = None) -> bool:
    """显示所有生效配置"""
    from mclang.build_profile import load_build_profile
    from ..toolchain import get_host_target

    target = target or get_host_target()
    toolchain_config, user_config, project_config = get_config_paths()

    print("配置文件：")
    print(f"  工具链: {toolchain_config} {'✓' if toolchain_config.exists() else '✗'}")
    print(f"  用户:   {user_config} {'✓' if user_config.exists() else '(未创建)'}")
    print(
        f"  项目:   {project_config} {'✓' if project_config.exists() else '(未创建)'}"
    )
    print()

    # 显示合并后的配置
    profile = load_build_profile(target, Path.cwd(), "debug")

    print("生效配置：")
    print(f"  compiler.cpp_std = {profile.compiler.cpp_std}")
    print(f"  compiler.args.common = {profile.compiler.args_common}")
    print(f"  compiler.args.debug = {profile.compiler.args_debug}")
    print(f"  compiler.args.release = {profile.compiler.args_release}")
    print(f"  compiler.defines.debug = {profile.compiler.defines_debug}")
    print(f"  compiler.defines.release = {profile.compiler.defines_release}")
    print(f"  linker.args.common = {profile.linker.args_common}")

    return True


def cmd_get(key: str, target: Optional[str] = None) -> bool:
    """获取配置值"""
    from mclang.build_profile import load_build_profile
    from ..toolchain import get_host_target

    target = target or get_host_target()
    profile = load_build_profile(target, Path.cwd(), "debug")

    # 映射键到 profile 属性
    key_map = {
        "compiler.cpp_std": profile.compiler.cpp_std,
        "compiler.args.common": profile.compiler.args_common,
        "compiler.args.debug": profile.compiler.args_debug,
        "compiler.args.release": profile.compiler.args_release,
        "compiler.defines.debug": profile.compiler.defines_debug,
        "compiler.defines.release": profile.compiler.defines_release,
        "linker.args.common": profile.linker.args_common,
    }

    if key in key_map:
        print(key_map[key])
        return True
    else:
        print(f"未知配置项: {key}")
        print("可用配置项:")
        for k in key_map:
            print(f"  {k}")
        return False


def cmd_set(key: str, value: str, scope: str = "global") -> bool:
    """设置配置值"""
    _, user_config, project_config = get_config_paths()

    if scope == "global":
        config_path = user_config
        section = None  # 直接写入根
    elif scope == "local":
        config_path = project_config
        section = "build"  # 写入 [build] 节
    else:
        print(f"未知 scope: {scope}")
        return False

    # 加载现有配置
    data = _load_toml(config_path)

    # 设置值
    if section:
        if section not in data:
            data[section] = {}
        _set_nested(data[section], key, value)
    else:
        _set_nested(data, key, value)

    # 保存
    _save_toml(config_path, data)
    print(f"已设置 {key} = {value}")
    print(f"配置文件: {config_path}")

    return True


def cmd_unset(key: str, scope: str = "global") -> bool:
    """删除配置值"""
    _, user_config, project_config = get_config_paths()

    if scope == "global":
        config_path = user_config
        section = None
    elif scope == "local":
        config_path = project_config
        section = "build"
    else:
        print(f"未知 scope: {scope}")
        return False

    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        return False

    data = _load_toml(config_path)

    if section:
        if section in data:
            if _unset_nested(data[section], key):
                _save_toml(config_path, data)
                print(f"已删除 {key}")
                return True
    else:
        if _unset_nested(data, key):
            _save_toml(config_path, data)
            print(f"已删除 {key}")
            return True

    print(f"配置项不存在: {key}")
    return False


def run_config(args) -> bool:
    """执行 config 命令"""
    # 确定 scope（默认 global）
    if getattr(args, "local", False):
        scope = "local"
    elif getattr(args, "global_scope", False):
        scope = "global"
    else:
        scope = "global"  # 默认

    target = getattr(args, "target", None)

    # 处理不同操作
    if getattr(args, "list", False):
        return cmd_list(target)

    if getattr(args, "get", None):
        return cmd_get(args.get, target)

    if getattr(args, "set", None):
        if len(args.set) != 2:
            print("用法: mcli config --set <key> <value>")
            return False
        return cmd_set(args.set[0], args.set[1], scope)

    if getattr(args, "unset", None):
        return cmd_unset(args.unset, scope)

    # 默认显示帮助
    return cmd_list(target)
