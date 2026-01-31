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
mcli create 命令 - 从模板创建 MCLang 项目

使用模板系统快速创建新项目，支持：
- bin 模板：可执行程序项目
- lib 模板：共享库项目
- toolchain 模板：工具链配置项目
"""

import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

import tomllib

from mcli.template import ProjectTemplate
from ..paths import get_mcli_root
from ..logging import get_logger


def _get_project_templates_dir() -> Path:
    return get_mcli_root() / "templates" / "project"


def _list_available_templates() -> List[str]:
    templates_dir = _get_project_templates_dir()
    if not templates_dir.exists():
        return []

    templates = []
    for item in templates_dir.iterdir():
        if item.is_dir() and not item.name.startswith("_") and not item.name.startswith("."):
            templates.append(item.name)
    return templates


def _get_template(template_name: str) -> Optional[ProjectTemplate]:
    templates_dir = _get_project_templates_dir()
    template_dir = templates_dir / template_name

    if not template_dir.exists():
        return None

    return ProjectTemplate(template_dir)


def parse_template_vars(var_list: List[str], logger=None) -> Dict[str, Any]:
    """解析模板变量（格式: name=value，支持类型推断）"""
    result = {}
    if not var_list:
        return result

    if logger is None:
        logger = get_logger("create", Path.cwd(), "debug")

    for var_str in var_list:
        if "=" not in var_str:
            logger.warning(f"忽略无效的变量格式 '{var_str}'，应为 name=value")
            continue

        name, value = var_str.split("=", 1)
        name = name.strip()
        value = value.strip()

        # 类型推断
        if value.lower() in ("true", "yes", "on"):
            result[name] = True
        elif value.lower() in ("false", "no", "off"):
            result[name] = False
        elif value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
            result[name] = int(value)
        elif _is_float(value):
            result[name] = float(value)
        else:
            result[name] = value

    return result


def _is_float(s: str) -> bool:
    """检查字符串是否为浮点数"""
    try:
        float(s)
        return "." in s or "e" in s.lower()
    except ValueError:
        return False


def show_template_help(template_name: str) -> bool:
    """显示模板的可配置变量"""
    logger = get_logger("create", Path.cwd(), "debug")
    template = _get_template(template_name)

    if template is None:
        logger.error(f"模板 '{template_name}' 不存在")
        logger.info(f"可用模板: {', '.join(_list_available_templates())}")
        return False

    print(f"模板: {template_name}")
    print(f"描述: {template.description or '无描述'}")
    print("")
    print("可配置变量:")

    if not template.variables:
        print("  (无)")
    else:
        for var_name, var_def in template.variables.items():
            required = "必需" if var_def.required else "可选"
            default = f"默认: {var_def.default}" if var_def.default is not None else "无默认值"
            desc = var_def.description or ""
            print(f"  {var_name:<20} {required:<6} {default:<20} {desc}")

    return True


def get_template_descriptions() -> Dict[str, str]:
    """获取所有模板的描述"""
    templates = {}
    for name in _list_available_templates():
        template = _get_template(name)
        if template:
            templates[name] = template.description
    return templates


def _create_project_from_template(
    template_name: str, project_dir: Path, context: Dict[str, Any]
) -> List[str]:
    """从工程模板创建项目"""
    template = _get_template(template_name)

    if template is None:
        raise ValueError(f"模板 '{template_name}' 不存在")

    # 合并默认变量值
    full_context = {}
    for var_name, var_def in template.variables.items():
        full_context[var_name] = var_def.get_value(context.get(var_name))

    # 添加用户提供的其他变量
    for key, value in context.items():
        if key not in full_context:
            full_context[key] = value

    return template.render_to_directory(project_dir, full_context)


def run_create(args) -> bool:
    """从模板创建项目"""
    logger = get_logger("create", Path.cwd(), "debug")

    # 处理 --list 选项
    if getattr(args, "list", False):
        templates = get_template_descriptions()

        print("可用模板:")
        for name, desc in templates.items():
            print(f"  {name:<15} - {desc or '无描述'}")
        return True

    # 处理 --help-template 选项
    if getattr(args, "help_template", None):
        return show_template_help(args.help_template)

    project_name = args.name
    if not project_name:
        logger.error("需要提供项目名称")
        logger.info("用法: mcli create <name> [-t <template>] [-V name=value ...]")
        logger.info("使用 --list 查看所有可用模板")
        return False

    template_type = args.template
    output_dir = args.output or Path.cwd()

    # 检查模板是否存在
    template = _get_template(template_type)
    if template is None:
        logger.error(f"模板 '{template_type}' 不存在")
        logger.info(f"可用模板: {', '.join(_list_available_templates())}")
        logger.info("使用 --list 查看所有可用模板")
        return False

    # 解析模板变量
    template_vars = parse_template_vars(args.var or [], logger)

    # 设置必需变量
    if "project_name" in template.variables:
        template_vars["project_name"] = project_name

    # 创建项目目录
    if args.output:
        project_dir = Path(output_dir) / project_name
    else:
        project_dir = Path.cwd() / project_name

    if project_dir.exists():
        logger.error(f"目录 '{project_dir}' 已存在")
        return False

    print(f"创建 {template_type} 项目: {project_name}")
    print(f"输出目录: {project_dir}")

    # 渲染模板
    try:
        created_files = _create_project_from_template(
            template_type, project_dir, template_vars
        )

        print(f"\n成功创建 {len(created_files)} 个文件:")
        for f in sorted(created_files):
            print(f"  {f}")

        # 安装依赖并创建 stub 软链接
        print("\n安装依赖...")
        from ..package.deps import sync_mclang_dir, install_conan_packages_for_project
        from mcli.toolchain.manager import get_toolchain_manager
        from mcli.toolchain.conan_profile import generate_conan_profile

        # 获取工具链用于生成 Conan profile
        profile_path = None
        try:
            tm = get_toolchain_manager()
            toolchain = tm.get_default()
            if toolchain:
                from mcli.toolchain import get_host_target
                # 使用 Debug 作为默认 build_type（项目初始化）
                profile_path = generate_conan_profile(
                    toolchain_name=toolchain.name,
                    toolchain_path=toolchain._toolchain_dir,
                    target=get_host_target(),
                    build_type="Debug",  # 默认使用 Debug
                    project_dir=project_dir,
                )
        except Exception as e:
            logger.warning(f"生成 Conan profile 失败: {e}")

        # 安装 Conan 依赖
        success = install_conan_packages_for_project(project_dir, profile_path)
        if success:
            print("  ✓ 依赖安装完成")

        # 同步 .mclang/ 目录（创建 stub 软链接）
        print("\n同步 .mclang/ 目录...")
        sync_mclang_dir(project_dir, verbose=True, logger=logger)
        print("  ✓ .mclang/ 目录已同步")

        print(f"\n下一步:")
        print(f"  cd {project_dir.name if not args.output else project_dir}")
        print(f"  mcli build")

        return True
    except Exception as e:
        logger.error(f"创建项目失败: {e}")
        return False


def setup_parser(subparsers):
    """设置 create 命令的参数解析器"""
    create_parser = subparsers.add_parser(
        "create",
        help="从模板创建 MCLang 项目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    create_parser.add_argument(
        "name",
        nargs="?",
        help="项目名称",
    )
    create_parser.add_argument(
        "-t",
        "--template",
        default="bin",
        help="项目模板 (bin=可执行程序, lib=共享库, toolchain=工具链配置)",
    )
    create_parser.add_argument(
        "-o",
        "--output",
        help="输出目录（默认为当前目录）",
    )
    create_parser.add_argument(
        "-V",
        "--var",
        action="append",
        metavar="NAME=VALUE",
        help="设置模板变量 (可多次使用，如 -V async=true -V threads=4)",
    )
    create_parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用模板",
    )
    create_parser.add_argument(
        "--help-template",
        metavar="TEMPLATE",
        help="显示指定模板的可配置变量",
    )

    return create_parser
