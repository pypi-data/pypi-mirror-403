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
mcli build 命令 - 构建 MCLang 项目

使用 Conan 构建系统编译项目，确保与运行时库 ABI 兼容。

核心设计：
- mcli build 调用 Conan 进行依赖管理和构建
- 构建参数（build_type）会被保存供 mcli run 使用
- 用户在 conanfile.py 中选择具体的构建工具（CMake、Meson 等）
"""

import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .. import BUILD_DIR_NAME
from ..toolchain.conan_profile import generate_conan_profile
from ..logging import get_logger
from ..paths import get_build_config_path


# 过滤噪音模式（保留原始字符串，不使用正则的转义）
NOISE_PATTERNS = [
    r'=+$',                           # 分隔线
    r'-+$',                           # 分隔线
    r'========+$',                    # Conan section 分隔线
    r'WARN: legacy:',                 # Conan legacy 警告
    r"Use [&|*]:toolchain=",          # Conan toolchain 提示
    r"or other pattern if the intent", # Conan toolchain 提示续
    r"Use '.*' to refer to",          # Conan "Use ... to refer" 提示
    r'Shell cwd was reset',           # Shell 重置信息
    r'^\s*$',                         # 空行
    r'^Profile (?:host|build):$',     # Profile 标题
    r'^\[settings\]$',                 # Profile [settings]
    r'^\[options\]$',                  # Profile [options]
    r'^\[conf\]$',                     # Profile [conf]
    r'^\[buildenv\]$',                 # Profile [buildenv]
    r'^\s{0,4}arch=',                 # Profile arch=
    r'^\s{0,4}build_type=',           # Profile build_type=
    r'^\s{0,4}compiler=',              # Profile compiler=
    r'^\s{0,4}compiler\.',             # Profile compiler.
    r'^\s{0,4}os=',                   # Profile os=
    r'^\s{0,4}toolchain=',             # Profile toolchain=
    r'^\s{0,4}tools\.build:',          # Profile tools.build:
    r'^\s{0,4}CC=',                   # Profile CC=
    r'^\s{0,4}CXX=',                  # Profile CXX=
    r'^-- The C compiler',             # CMake 检测编译器
    r'^-- The CXX compiler',           # CMake 检测编译器
    r'^-- Detecting C compiler',       # CMake Detecting
    r'^-- Detecting CXX compiler',     # CMake Detecting
    r'^-- Conan toolchain: Defining',  # Conan toolchain 详情
    r'^-- Conan: Component target',    # Conan 组件目标
    r'^-- Conan: Target declared',     # Conan 目标声明
    r'^\s{0,4}find_package\(',        # CMake 提示
    r'^\s{0,4}target_link_libraries\(', # CMake 提示
    r'^\s{0,4}\(cmake>=',             # CMake 提示
    r'^\s{0,4}\(cmake<',              # CMake 提示
    # Conan generate 技术细节（install 阶段过滤）
    r': Generators folder:',          # 生成器目录
    r': CMakeDeps necessary',         # CMakeDeps 提示
    r': CMakeToolchain generated:',   # CMakeToolchain 生成
    r': CMakeToolchain: Preset',      # CMakeToolchain preset
    r': CMakeToolchain generated:.*\.json',  # CMakePresets/CMakeUserPresets 生成
    r'Generated CMake fragment:',     # CMake 片段
    r'Build config:',                 # 构建配置
    r': Generating aggregated env files',  # 环境变量文件生成
    r': Generated aggregated env files:',  # 环境变量文件生成结果
]

# build 阶段额外过滤的模式（conan build 会重新运行 generate，显示重复信息）
BUILD_PHASE_NOISE_PATTERNS = [
    r'Graph root',                    # 依赖图根节点
    r'Requirements$',                 # 依赖需求（标题行）
    r'\): /',                         # 包路径信息行（如 conanfile.py (hello/0.1.0): /Users/...）
    r'[\w./]+/[\d.]+#',              # 包缓存信息行（如 mcl_runtime/0.1.0#... - Cache）
    r': Already installed!',          # 已安装提示
    r': Calling generate\(\)',         # generate() 调用
    r': Generators folder:',          # 生成器目录
    r': CMakeDeps necessary',         # CMakeDeps 提示
    r': CMakeToolchain generated:',   # CMakeToolchain 生成
    r': CMakeToolchain: Preset',      # CMakeToolchain preset
    r': CMakeToolchain generated:.*CMakePresets\.json',  # CMakePresets 生成
    r': CMakeToolchain generated:.*CMakeUserPresets\.json',  # CMakeUserPresets 生成
    r': Generating C\+\+ from',       # C++ 代码生成
    r':   \[skip\]',                  # 跳过生成
    r':   Generated \d+ files to:',   # 生成文件数
    r':   Generated CMake fragment:', # CMake 片段
    r':   Build config:',             # 构建配置
    r': Generating aggregated env files',  # 环境变量文件生成
    r': Generated aggregated env files:',  # 环境变量文件生成结果
    r'======== (?:Computing dependency graph|Computing necessary packages|Installing packages|Finalizing install)',  # Conan 步骤标题
]


def _should_filter_line(line: str, is_build_phase: bool = False) -> bool:
    """判断是否过滤输出行（保留颜色码）"""
    # 移除 ANSI 颜色码后再匹配
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    clean_line = ansi_escape.sub('', line)
    # 移除行尾的 \r\n 以匹配模式
    clean_line = clean_line.rstrip('\r\n')

    # 通用噪音模式
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, clean_line):
            return True

    # build 阶段额外的过滤（过滤 conan build 重复运行的 generate 输出）
    if is_build_phase:
        for pattern in BUILD_PHASE_NOISE_PATTERNS:
            if re.search(pattern, clean_line):
                return True

    return False


def _run_with_filter(cmd, cwd, log_file=None, is_build_phase=False, verbose=False):
    """运行命令并过滤输出（保留颜色）"""
    import os
    from datetime import datetime

    # 直接运行命令，不使用 script（跨平台）
    # 如果 verbose=True，添加环境变量让构建工具显示详细输出
    env = os.environ.copy()
    if verbose:
        env['VERBOSE'] = '1'
        env['CMAKE_COLOR_DIAGNOSTICS'] = 'ON'
    # 强制开启颜色输出
    env['CLICOLOR_FORCE'] = '1'

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        cwd=cwd,
        env=env,
    )

    # 逐行读取输出（保留字节，以保留 ANSI 颜色码）
    line_count = 0
    for line in iter(process.stdout.readline, b''):
        line_count += 1

        # 解码为字符串
        try:
            line_str = line.decode('utf-8')
        except UnicodeDecodeError:
            line_str = line.decode('utf-8', errors='replace')

        # 写入日志文件（原始输出）
        if log_file:
            log_file.write(line_str)
            log_file.flush()

        # 过滤后输出到终端
        if not _should_filter_line(line_str, is_build_phase):
            # 为非空行添加时间戳（跳过已有时间戳的行）
            if line_str.strip():
                # 检查是否已有时间戳（HH:MM:SS 格式）
                has_timestamp = False
                ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
                clean_start = ansi_escape.sub('', line_str[:20])
                # 检查是否以时间戳格式开始（HH:MM:SS 或 ANSI+时间戳）
                if clean_start and len(clean_start) >= 8:
                    # 检查是否匹配 HH:MM:SS 格式
                    time_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}\s')
                    if time_pattern.match(clean_start):
                        has_timestamp = True

                if not has_timestamp:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    # 在行首添加时间戳（在 ANSI 颜色码之前）
                    if clean_start and not clean_start[0].isspace():
                        # 行首有内容，添加时间戳
                        # 检查是否以 ANSI 颜色码开始
                        if line_str.startswith('\x1b['):
                            # 找到颜色码结束位置
                            end_idx = line_str.find('m', 0, 20)
                            if end_idx != -1:
                                # 在颜色码后插入时间戳
                                line_str = line_str[:end_idx+1] + timestamp + ' ' + line_str[end_idx+1:]
                            else:
                                line_str = timestamp + ' ' + line_str
                        else:
                            line_str = timestamp + ' ' + line_str
            sys.stdout.write(line_str)
            sys.stdout.flush()

    process.wait()

    return process.returncode



def run_build_conan(args, project_dir: Path, toolchain_name: Optional[str], build_type: str, for_test: bool = False) -> bool:
    """使用 Conan 构建项目，保存配置供 mcli run 使用"""
    from ..toolchain import get_host_target
    from ..toolchain.manager import get_toolchain_manager
    import sys
    import os

    verbose = getattr(args, "verbose", False)
    target = getattr(args, "target", None)
    parallel_jobs = getattr(args, "parallel_jobs", None)
    conan_options = getattr(args, "conan_options", []) or []

    # 获取日志记录器
    logger = get_logger("build", project_dir, build_type.lower())

    # 查找 conan 可执行文件
    conan_exe = shutil.which("conan")
    if not conan_exe:
        # 如果 PATH 中找不到，尝试在 venv/bin 中查找
        if sys.executable:
            bin_dir = Path(sys.executable).parent
            conan_in_venv = bin_dir / "conan"
            if conan_in_venv.exists():
                conan_exe = str(conan_in_venv)
        if not conan_exe:
            logger.error("未找到 conan 命令")
            return False

    # 确定目标平台
    host_target = get_host_target()
    if target is None:
        target = host_target

    # 获取工具链
    tm = get_toolchain_manager()
    if toolchain_name:
        toolchain = tm.get_toolchain(toolchain_name)
        if not toolchain:
            logger.error(f"工具链 '{toolchain_name}' 不存在")
            return False
    else:
        # 用户未指定 toolchain，使用默认工具链
        toolchain = tm.get_default()
        if not toolchain:
            logger.error("未配置工具链")
            return False

    # 生成 conanbase.py（直接从 service.json 读取配置）
    _ensure_conanbase_in_project(project_dir, logger, toolchain_name=toolchain.name)

    # 输出构建配置
    logger.info(f"构建配置: toolchain={toolchain.name}, target={target}, build_type={build_type}")

    # 生成 Conan profile
    logger.debug("生成 Conan profile...")
    try:
        profile_path = generate_conan_profile(
            toolchain_name=toolchain.name,
            toolchain_path=toolchain._toolchain_dir,
            target=target,
            build_type=build_type,
            project_dir=project_dir,
            parallel_jobs=parallel_jobs,
        )
        logger.debug(f"  Profile: {profile_path.relative_to(project_dir)}")
    except Exception as e:
        logger.error(f"生成 Conan profile 失败: {e}")
        return False

    from ..paths import get_build_dir
    log_dir = get_build_dir(project_dir, toolchain.name, target, build_type)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / "build.log"
    log_file = open(log_file_path, 'w', encoding='utf-8')

    # 执行 conan install
    logger.info("配置依赖...")
    conan_install_cmd = [
        conan_exe, "install", ".",
        "-pr:h", str(profile_path),
        "-pr:b", str(profile_path),
        "--build=missing",  # 远端没有匹配包时自动从源码构建
    ]
    if for_test:
        conan_install_cmd.extend(["-o", "test=True"])
    # 添加用户指定的 conan 选项
    for option in conan_options:
        conan_install_cmd.extend(["-o", option])
    if verbose:
        conan_install_cmd.append("-v")

    logger.debug(f"执行: {' '.join(conan_install_cmd)}")
    returncode = _run_with_filter(conan_install_cmd, project_dir, log_file, verbose=verbose)

    if returncode != 0:
        logger.error("配置依赖失败")
        log_file.close()
        return False

    # 执行 conan build
    logger.info("编译项目...")
    conan_build_cmd = [
        conan_exe, "build", ".",
        "-pr:h", str(profile_path),
        "-pr:b", str(profile_path),
    ]
    if for_test:
        conan_build_cmd.extend(["-o", "test=True"])
    # 添加用户指定的 conan 选项
    for option in conan_options:
        conan_build_cmd.extend(["-o", option])
    if verbose:
        conan_build_cmd.append("-v")

    logger.debug(f"执行: {' '.join(conan_build_cmd)}")
    returncode = _run_with_filter(conan_build_cmd, project_dir, log_file, is_build_phase=True, verbose=verbose)

    log_file.close()

    if returncode != 0:
        logger.error("编译失败")
        return False

    # **保存构建配置**：供 mcli run 使用
    build_config_path = get_build_config_path(project_dir)
    build_config_path.parent.mkdir(parents=True, exist_ok=True)
    build_config = {
        "toolchain": toolchain.name,
        "target": target,
        "build_type": build_type.lower(),
    }
    with open(build_config_path, "w") as f:
        json.dump(build_config, f, indent=2)
    logger.debug(f"✓ 构建配置已保存: {build_config_path.relative_to(project_dir)}")

    logger.info("✓ 构建完成")
    return True


def run_build(args) -> bool:
    """构建项目"""
    from ..config import ProjectConfig

    project_dir = Path.cwd()
    logger = get_logger("build", project_dir, "debug")

    # **检查并读取 service.json**（只读取一次）
    project_config_obj = ProjectConfig(project_dir)
    if not project_config_obj.service_json_path.exists():
        logger.error(f"未找到 {project_config_obj.service_json_path}，请在 MCLang 项目目录中运行此命令")
        return False

    # **解析 service.json**（整个构建过程只读取一次）
    try:
        project_config = project_config_obj.load()
    except Exception as e:
        logger.error(f"无法解析 service.json: {e}")
        return False

    # 检查是否存在 conanfile.py
    conanfile = project_dir / "conanfile.py"
    if not conanfile.exists():
        logger.error("未找到 conanfile.py")
        logger.info("提示: MCLang 项目需要使用 Conan 构建系统")
        return False

    verbose = getattr(args, "verbose", False)
    target = getattr(args, "target", None)
    toolchain_name = getattr(args, "toolchain", None)
    build_type = args.bt.capitalize()  # "debug" or "release" -> "Debug" or "Release"

    return run_build_conan(args, project_dir, toolchain_name, build_type)


def _ensure_conanbase_in_project(project_dir: Path, logger, toolchain_name: str = "default") -> None:
    """使用模板引擎生成 conanbase.py

    从 service.json 读取配置，使用模板引擎生成 conanbase.py。

    Args:
        project_dir: 项目目录
        logger: 日志记录器
        toolchain_name: 工具链名称（用于构建目录命名）
    """
    from ..paths import get_templates_dir
    from ..template import ProjectTemplate
    from ..config import ProjectConfig
    import shutil

    conanbase_dest = project_dir / "conanbase.py"
    template_dir = get_templates_dir()
    template_file = template_dir / "conanbase.py.mct"

    # 直接从 service.json 读取配置（确保使用最新版本）
    config_obj = ProjectConfig(project_dir)
    try:
        service_json = config_obj.load()
    except FileNotFoundError:
        logger.warning(f"未找到 service.json，跳过生成 conanbase.py")
        return
    except Exception as e:
        logger.warning(f"读取 service.json 失败: {e}")
        return

    # 准备模板上下文
    project_version = service_json.get("version", "0.0.0")

    # 工具链名称（用于构建目录命名）
    context = {
        "project_version": project_version,
        "conan_requires": [],  # 将在后面填充
        "conan_test_requires": [],  # 将在后面填充
        "build_dir_name": BUILD_DIR_NAME,
        "toolchain_name": toolchain_name,  # 工具链名称
    }

    # 解析 dependencies.build 中的 conan 依赖（从 service_json 读取）
    dependencies = service_json.get("dependencies", {})
    build_deps = dependencies.get("build", [])
    conan_requires = []
    for dep in build_deps:
        if isinstance(dep, dict) and "conan" in dep:
            conan_requires.append(dep["conan"])

    test_deps = dependencies.get("test", [])
    conan_test_requires = []
    for dep in test_deps:
        if isinstance(dep, dict) and "conan" in dep:
            conan_test_requires.append(dep["conan"])

    # 更新 context 中的依赖列表
    context["conan_requires"] = conan_requires
    context["conan_test_requires"] = conan_test_requires

    # 使用模板引擎生成 conanbase.py
    if template_file.exists():
        try:
            # 读取模板内容
            with open(template_file, "r", encoding="utf-8") as f:
                template_content = f.read()

            # 简单的模板渲染（使用内置的模板引擎）
            template = ProjectTemplate(template_file.parent)
            rendered = template._render_template(template_content, context)

            # 写入目标文件
            with open(conanbase_dest, "w", encoding="utf-8") as f:
                f.write(rendered)

            logger.debug(f"✓ 已生成 conanbase.py (version={project_version}, build_deps={len(conan_requires)}, test_deps={len(conan_test_requires)})")
        except Exception as e:
            logger.warning(f"生成 conanbase.py 失败: {e}")
    else:
        logger.warning(f"未找到 conanbase.py 模板: {template_file}")

