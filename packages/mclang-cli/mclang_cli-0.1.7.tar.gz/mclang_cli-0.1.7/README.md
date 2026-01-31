# MCLang CLI - MCLang 项目管理工具

MCLang CLI (mcli) 是 MCLang 工具链的命令行项目管理工具，提供项目创建、构建、依赖管理等功能。

## 🚀 特性

- **项目创建**: 快速创建 MCLang 项目
- **依赖管理**: 基于 Conan 的 C++ 依赖管理
- **构建管理**: 支持多种工具链（Clang、GCC、Zig）
- **模板系统**: 内置项目模板和 stub 文件生成

## 📦 安装

```bash
pip install mclang-cli
```

安装后使用 `mcli` 命令：

```bash
mcli --version
```

或从源码安装：

```bash
git clone https://gitcode.com/zjp99/mcli.git
cd mcli
pip install -e . --force-reinstall --no-deps

# 安装到全局环境
pip install -e . --break-system-packages --force-reinstall --no-deps
```

**注意**: 安装 mclang-cli 会自动安装 mclang-compiler 作为依赖。

## 🔧 使用方法

### mcli 项目管理

```bash
# 创建新项目
mcli create my-project --template lib

# 构建项目
mcli build

# 构建并运行
mcli run

# 运行测试
mcli test

# 依赖管理（使用 Conan）
conan install . --user=dev

# 发布包
mcli publish --channel stable -bt release

# 工具链管理
mcli toolchain list
mcli toolchain add zig
mcli toolchain remove gcc
mcli toolchain set-default zig
mcli toolchain info zig

# 配置管理
mcli config
mcli config set default_toolchain zig
mcli config default_target
```

### 项目配置

项目使用 `mds/service.json` 进行配置：

```json
{
    "name": "my-project",
    "version": "1.0.0",
    "type": "library",
    "author": "Your Name",
    "license": "Mulan PSL v2",
    "description": "Project description",
    "dependencies": {
        "build": [
            {"conan": "boost/[>=1.87.0]"}
        ]
    },
    "mclang": {
        "type": "native",
        "stubs": {
            "dir": "stubs",
            "packages": ["mc", "gtest"]
        }
    }
}
```

## 📝 命令参考

### create - 创建项目

```bash
mcli create <project-name> [options]

选项:
  -t, --template TYPE  项目模板 (bin/lib, 默认: bin)
  --list              列出所有可用模板
```

### build - 构建项目

```bash
mcli build [options]

选项:
  --bt, --build-type TYPE  构建类型 (debug/release, 默认: debug)
  --channel STAGE           构建阶段 (dev/rc/stable, 默认: dev)
  --toolchain NAME        工具链名称
  --target TRIPLE         目标平台 (如 linux-aarch64, 用于交叉编译)
  -j, --jobs NUM          并行构建任务数
  -v, --verbose           详细输出
```

### run - 构建并运行

```bash
mcli run [options] [-- <args>]

选项:
  --bt, --build-type TYPE  构建类型
  --channel STAGE           构建阶段
  --toolchain NAME        工具链名称
  --target TRIPLE         目标平台
  --                      分隔符，后面传递给程序的参数

示例:
  mcli run                               # 使用上次构建配置运行
  mcli run --channel stable -bt release    # 指定构建参数运行
  mcli run -- --arg1 --arg2              # 传递参数给程序
```

### test - 运行测试

```bash
mcli test [test_names] [options] [-- <framework-args>]

选项:
  --bt, --build-type TYPE  构建类型 (debug/release)
  --channel STAGE           构建阶段 (dev/rc/stable)
  --toolchain NAME        工具链名称
  --target TRIPLE         目标平台
  -j, --jobs NUM          并行构建任务数
  -v, --verbose           mcli 详细输出（CTest -V）
  --                      分隔符，后面传递给测试框架的参数

使用 -- 分隔符：
  -- 之前：mcli 参数（测试名称用于 CTest -R 筛选）
  -- 之后：直接转发给测试框架（绕过 argparse 识别）

示例:
  mcli test                                  # 运行所有测试
  mcli test mcc_gtests                      # 运行指定测试
  mcli test mcc_gtests mcc_pytests          # 运行多个测试
  mcli test mcc_pytests -- test_lambda.py   # 转发参数给测试框架
  mcli test mcc_pytests -- -v               # pytest 详细输出
  mcli test mcc_gtests -- --gtest_filter=*Arc*  # GoogleTest filter
  mcli test -v mcc_pytests -- -v            # mcli 和 pytest 都详细输出
```

### 依赖管理

```bash
# 刷新依赖（更新 stub 文件）
mcli reload

# 刷新稳定版本依赖
mcli reload --channel stable -bt release

# 使用 Conan 安装依赖
conan install . --user=dev

# 查看已安装的包
conan list
```

### toolchain - 工具链管理

```bash
mcli toolchain list                              # 列出所有工具链
mcli toolchain add <type> [options]              # 添加工具链
mcli toolchain remove <name>                     # 移除工具链
mcli toolchain set-default <name>                # 设置默认工具链
mcli toolchain info <name>                       # 显示工具链详情

添加工具链选项:
  --name NAME      工具链名称（默认为编译器类型）
  --path PATH      编译器路径
  --set-default    添加后设为默认

支持的编译器类型: gcc, clang, zig

示例:
  mcli toolchain add zig                              # 添加 Zig 工具链
  mcli toolchain add gcc --name my-gcc                # 指定名称
  mcli toolchain add clang --path /opt/llvm/bin/clang # 指定路径
  mcli toolchain add zig --set-default                # 添加并设为默认
```

### config - 配置管理

```bash
mcli config                        # 查看所有配置
mcli config <key>                  # 查看特定配置项
mcli config set <key> <value>      # 设置配置项

示例:
  mcli config set default_toolchain zig    # 设置默认工具链
  mcli config set default_target linux-x86_64  # 设置默认目标平台
  mcli config default_toolchain            # 查看默认工具链
```

### publish - 发布包

```bash
mcli publish [options]

选项:
  --channel STAGE      发布阶段 (dev/rc/stable, 默认: dev)
  --bt, --build-type TYPE  构建类型 (debug/release)
  --user USER        Conan 包所有者 (默认: openubmc)
  --no-upload        只打包到本地缓存，不上传

Conan 包版本格式: {name}/{version}@{user}/{channel}

示例:
  mcli publish --channel stable -bt release              # 发布稳定版本
  mcli publish --user myorg --channel stable -bt release # 指定所有者
  mcli publish --no-upload                             # 只打包不上传
```

## 🏗️ 架构

```
mcli/
├── mcli/                  # CLI 工具核心
│   ├── commands/          # 命令实现
│   │   ├── create.py      # 项目创建
│   │   ├── build.py       # 构建管理
│   │   ├── deps.py        # 依赖管理
│   │   └── publish.py     # 包发布
│   ├── toolchain/         # 工具链管理（内部模块）
│   │   ├── base.py        # 工具链基类
│   │   ├── zig.py         # Zig 工具链
│   │   ├── system.py      # 系统工具链 (GCC/Clang)
│   │   └── manager.py     # 工具链管理器
│   ├── package/           # 包管理（内部模块）
│   │   ├── manager.py     # 包管理器
│   │   ├── conan.py       # Conan 集成
│   │   └── abi.py         # ABI 管理
│   ├── template.py        # 模板引擎（内置，支持 {{ }} 和 {% %} 语法）
│   ├── paths.py           # 路径工具
│   ├── logging.py         # 日志系统
│   └── config.py          # 配置管理
└── templates/             # 项目模板
    ├── conanbase.py.mct   # Conan 基类模板（自动生成到用户项目）
    ├── bin/               # 可执行程序模板
    ├── lib/               # 库项目模板
    └── toolchain/         # 工具链配置模板
```

**设计说明**：
- `mcli/` 包含 CLI 的所有核心代码
- `template.py` 是内置的模板引擎，支持 {{ }} 和 {% %} 语法
- `toolchain/` 和 `package/` 是内部实现模块
- `templates/conanbase.py.mct` 是 Conan 基类模板，mcli build 时自动生成到用户项目目录
- 用户项目的 `conanfile.py` 通过 `from conanbase import ConanBase` 导入生成的基类
- `templates/` 存放项目模板文件

## 📚 文档

- [MCLang CLI 使用指南](docs/mcli_guide.md) - 完整的命令参考和使用说明

## 🔌 依赖关系

mcli 依赖于以下组件：

- **mclang-compiler**: 编译器核心（自动安装）
- **conan**: C++ 包管理器（>= 2.0.0）

**构建系统**：mcli 使用 Conan 进行依赖管理和构建，用户可在项目的 `conanfile.py` 中选择具体的构建工具（CMake、Meson 等）。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

Mulan PSL v2 - 详见 [LICENSE](LICENSE) 文件
