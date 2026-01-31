"""
MCLang CLI - MCLang 项目管理工具

这是 MCLang 工具链的命令行界面，提供：
- 项目创建（mcli create）
- 工具链设置（mcli setup）
- 项目构建（mcli build）
- 测试运行（mcli test/run）
- 依赖管理（mcli reload/install）
- 包发布（mcli publish）
- 工具链管理（mcli toolchain）
- 配置管理（mcli config）
"""

from setuptools import setup
from pathlib import Path
import tomllib

# 从 pyproject.toml 读取版本号（唯一来源）
pyproject_file = Path(__file__).parent / "pyproject.toml"
with open(pyproject_file, "rb") as f:
    pyproject = tomllib.load(f)
    version = pyproject["project"]["version"]

# 检查 service.json 版本号是否一致
service_file = Path(__file__).parent / "mds" / "service.json"
if service_file.exists():
    import json
    with open(service_file, "r", encoding="utf-8") as f:
        service = json.load(f)
        service_version = service.get("version")
        if service_version != version:
            raise SystemExit(
                f"错误: 版本号不一致!\n"
                f"  pyproject.toml: {version}\n"
                f"  mds/service.json: {service_version}\n"
                f"请统一版本号后再安装。"
            )

# 读取README文件
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text(encoding="utf-8").strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

# 添加对 mclang-compiler 的依赖
requirements.append("mclang-compiler>=0.3.0,<0.4.0")

setup(
    name="mclang-cli",
    version=version,
    author="MCLang Development Team",
    author_email="mcli@example.com",
    description="MCLang CLI - MCLang 项目管理工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitcode.com/zjp99/mcli",
    packages=["mcli"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: Mulan PSL v2",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: C++",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        "mcli": [
            "*.pyi",
            "templates/**/*.toml",
            "templates/**/*.mct",
            "templates/**/*.json",
            "templates/**/.gitignore",
        ],
    },
    entry_points={
        "console_scripts": [
            # mcli - MCLang 命令行工具
            "mcli=mcli.main:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://gitcode.com/zjp99/mcli/issues",
        "Source": "https://gitcode.com/zjp99/mcli",
        "Documentation": "https://gitcode.com/zjp99/mcli",
    },
)
