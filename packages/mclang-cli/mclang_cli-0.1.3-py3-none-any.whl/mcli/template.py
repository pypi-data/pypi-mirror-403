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
MCLang 项目模板系统

提供可扩展的项目模板机制，支持：
- 基于目录的模板组织
- 类 Jinja2 语法的简单模板引擎（支持 {{ }} 和 {% %}）
- 模板元数据定义
- 动态模板发现
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

import tomllib


class TemplateError(Exception):
    """模板处理错误"""

    pass


class TemplateVariable:
    """模板变量定义"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.required = config.get("required", False)
        self.default = config.get("default", None)
        self.description = config.get("description", "")
        # 命令行参数相关
        self.cli_arg = config.get("cli_arg", False)  # 是否作为命令行参数
        self.cli_type = config.get("type", self._infer_type())  # 参数类型
        self.cli_short = config.get("short")  # 短参数，如 -t

    def _infer_type(self) -> str:
        """从默认值推断类型"""
        if self.default is None:
            return "str"
        if isinstance(self.default, bool):
            return "bool"
        if isinstance(self.default, int):
            return "int"
        if isinstance(self.default, float):
            return "float"
        return "str"

    def get_value(self, provided: Optional[Any] = None) -> Any:
        """获取变量值，优先使用提供的值，否则使用默认值"""
        if provided is not None:
            return provided
        if self.required and self.default is None:
            raise TemplateError(f"变量 '{self.name}' 是必需的")
        return self.default

    def get_cli_args(self) -> Dict[str, Any]:
        """获取 argparse 参数配置"""
        if not self.cli_arg:
            return {}

        kwargs: Dict[str, Any] = {}
        kwargs["help"] = self.description or f"模板变量 {self.name}"

        if self.cli_type == "bool":
            kwargs["action"] = "store_true"
            kwargs["default"] = self.default or False
        else:
            if self.cli_type == "int":
                kwargs["type"] = int
            elif self.cli_type == "float":
                kwargs["type"] = float
            kwargs["default"] = self.default

        return kwargs


class ProjectTemplate:
    """项目模板"""

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.name = template_dir.name
        self.metadata = self._load_metadata()
        self.variables = self._parse_variables()

    def _load_metadata(self) -> Dict[str, Any]:
        metadata_file = self.template_dir / "template.toml"
        if not metadata_file.exists():
            return {"template": {"name": self.name, "description": ""}}

        with open(metadata_file, "rb") as f:
            return tomllib.load(f)

    def _parse_variables(self) -> Dict[str, TemplateVariable]:
        variables = {}
        var_config = self.metadata.get("variables", {})
        for name, config in var_config.items():
            if isinstance(config, dict):
                variables[name] = TemplateVariable(name, config)
            else:
                # 简单值作为默认值
                variables[name] = TemplateVariable(name, {"default": config})
        return variables

    @property
    def description(self) -> str:
        return self.metadata.get("template", {}).get("description", "")

    def get_cli_variables(self) -> Dict[str, TemplateVariable]:
        return {
            name: var for name, var in self.variables.items() if var.cli_arg
        }

    def get_template_files(self) -> List[Path]:
        files = []
        for root, _, filenames in os.walk(self.template_dir):
            for filename in filenames:
                if filename.endswith(".mct"):
                    files.append(Path(root) / filename)
        return files

    def get_static_files(self) -> List[Path]:
        files = []
        for root, _, filenames in os.walk(self.template_dir):
            for filename in filenames:
                if not filename.endswith(".mct") and filename != "template.toml":
                    files.append(Path(root) / filename)
        return files

    def render_file(self, template_file: Path, context: Dict[str, Any]) -> str:
        with open(template_file, "r", encoding="utf-8") as f:
            content = f.read()
        return self._render_template(content, context)

    def _render_template(self, content: str, context: Dict[str, Any]) -> str:
        """使用自定义模板引擎渲染（支持 {{ }} 和 {% %} 语法）"""
        # 编译模板为 Python 代码
        code = self._compile_template(content)
        # 执行编译后的代码
        exec_locals = {}
        exec(code, {**context, "_result": []}, exec_locals)
        return exec_locals.get("_rendered", "")

    def _compile_template(self, content: str) -> str:
        r"""把模板编译成 Python 代码

        模板语法规则：
        - {{ expr }}: Python 表达式，输出结果
        - {% code %}: Python 控制块，不输出
        - {%- ... -%}, {{- ... -}}: 去除标签前后的空白字符（空格、制表符、换行符）
        - 单个 { 和 } 是普通字符，不需要转义
        - 在 block_code 内部跳过 Python 字符串（''、""、''''''、""""""）
        """
        # 状态定义
        STATE_TEXT = 0           # 普通文本
        STATE_EXPR = 1           # {{ 表达式块
        STATE_CODE = 2           # {% 控制块
        STATE_CODE_STRING = 3    # 控制块内的字符串（跳过模板语法）

        code_lines = ['_result = []']
        indent_stack = [0]
        INDENT_SIZE = 4

        state = STATE_TEXT
        in_string_char = None  # 当前字符串的引号字符
        escape_next = False
        skip_leading_whitespace = False  # 下一个文本块是否跳过前导空白

        i = 0
        n = len(content)
        text_start = 0
        expr_start = 0
        code_start = 0

        while i < n:
            c = content[i]

            if state == STATE_TEXT:
                # 检测 {{ 开始（表达式块）
                if c == '{' and i + 1 < n and content[i + 1] == '{':
                    tag_start = i  # 记住标签开始位置
                    i += 2
                    if i < n and content[i] == '-':
                        i += 1
                        trim_leading = True
                    else:
                        trim_leading = False
                    expr_start = i

                    # 保存之前的文本（可能需要去除尾部空白）
                    if text_start < tag_start:
                        text_to_save = content[text_start:tag_start]
                        # 如果有 {{-，去除前面的空白
                        if trim_leading:
                            text_to_save = text_to_save.rstrip()
                        self._append_text_code(text_to_save, code_lines, indent_stack[-1], skip_leading_whitespace)

                    state = STATE_EXPR
                    continue

                # 检测 {% 开始（控制块）
                if c == '{' and i + 1 < n and content[i + 1] == '%':
                    tag_start = i  # 记住标签开始位置
                    i += 2
                    if i < n and content[i] == '-':
                        i += 1
                        trim_leading = True
                    else:
                        trim_leading = False
                    code_start = i

                    # 保存之前的文本（可能需要去除尾部空白）
                    if text_start < tag_start:
                        text_to_save = content[text_start:tag_start]
                        # 如果有 {%-，去除前面的空白
                        if trim_leading:
                            text_to_save = text_to_save.rstrip()
                        self._append_text_code(text_to_save, code_lines, indent_stack[-1], skip_leading_whitespace)

                    state = STATE_CODE
                    continue
                i += 1

            elif state == STATE_EXPR:
                # 检测 }} 结束
                if c == '}' and i + 1 < n and content[i + 1] == '}':
                    # 检查前面是否有 dash（-}}）
                    expr_end = i
                    if expr_end > expr_start and content[expr_end - 1] == '-':
                        expr_end -= 1
                        trim_trailing = True
                    else:
                        trim_trailing = False

                    i += 2
                    expr = content[expr_start:expr_end].strip()
                    code_lines.append(' ' * indent_stack[-1] + f"_result.append(str({expr}))")

                    # 如果有 -}}，标记下一个文本块需要跳过前导空白
                    skip_leading_whitespace = trim_trailing
                    text_start = i  # 下一个文本从这里开始
                    state = STATE_TEXT
                    continue
                i += 1

            elif state == STATE_CODE:
                # 检测字符串开始
                if c in ('"', "'") and not escape_next:
                    # 检查是否有前缀（f、r 等）
                    j = i - 1
                    while j >= 0 and content[j] in 'fFrRuUbB':
                        j -= 1
                    # 只有当字符串前面是空白或运算符时才算字符串前缀
                    if j < 0 or content[j] in ' \t\n\r:([{,=+-*/%|&^~!<>':
                        if content[i:i+3] in ('"""', "'''"):
                            in_string_char = content[i:i+3]
                            i += 3
                        else:
                            in_string_char = c
                            i += 1
                        state = STATE_CODE_STRING
                        continue
                # 处理转义
                if c == '\\' and not escape_next:
                    escape_next = True
                    i += 1
                    continue
                # 检测 %} 结束
                if c == '%' and i + 1 < n and content[i + 1] == '}':
                    # 检查前面是否有 dash（-%}）
                    code_end = i
                    if code_end > code_start and content[code_end - 1] == '-':
                        code_end -= 1
                        trim_trailing = True
                    else:
                        trim_trailing = False

                    i += 2
                    code = content[code_start:code_end].strip()

                    # 处理控制块代码
                    if code in ('endfor', 'endif'):
                        if len(indent_stack) > 1:
                            indent_stack.pop()
                    elif code == 'else' or code.startswith('elif '):
                        # else/elif 应该与对应的 if/for 对齐，使用上一级缩进
                        parent_indent = indent_stack[-2] if len(indent_stack) > 1 else indent_stack[-1]
                        if not code.endswith(':'):
                            code += ':'
                        code_lines.append(' ' * parent_indent + code)
                        # 先 pop 当前的缩进级别
                        if len(indent_stack) > 1:
                            indent_stack.pop()
                        # 再 push 新的缩进级别
                        indent_stack.append(parent_indent + INDENT_SIZE)
                    elif code.startswith(('for ', 'if ', 'while ')):
                        # 先用当前缩进添加控制语句
                        if not code.endswith(':'):
                            code += ':'
                        code_lines.append(' ' * indent_stack[-1] + code)
                        # 然后增加缩进级别
                        indent_stack.append(indent_stack[-1] + INDENT_SIZE)
                    else:
                        code_lines.append(' ' * indent_stack[-1] + code)

                    # 如果有 -%}，标记下一个文本块需要跳过前导空白
                    skip_leading_whitespace = trim_trailing
                    text_start = i  # 下一个文本从这里开始
                    state = STATE_TEXT
                    continue
                i += 1

            elif state == STATE_CODE_STRING:
                # 在字符串内，跳过所有模板语法
                if escape_next:
                    escape_next = False
                    i += 1
                    continue
                if c == '\\':
                    escape_next = True
                    i += 1
                    continue
                # 检查字符串结束
                if in_string_char and len(in_string_char) == 3:
                    if i + 2 < n and content[i:i+3] == in_string_char:
                        in_string_char = None
                        state = STATE_CODE
                        i += 3
                else:
                    if c == in_string_char:
                        in_string_char = None
                        state = STATE_CODE
                        i += 1
                    else:
                        i += 1
                continue

            # 重置转义标志
            if escape_next and c != '\\':
                escape_next = False

        # 输出剩余的普通文本
        if text_start < n:
            self._append_text_code(content[text_start:], code_lines, indent_stack[-1], skip_leading_whitespace)

        code_lines.append('_rendered = "".join(_result)')
        return '\n'.join(code_lines)

    def _append_text_code(self, text: str, code_lines: list, indent: int, skip_leading: bool = False) -> None:
        """添加文本输出代码

        Args:
            text: 要输出的文本
            code_lines: 代码行列表
            indent: 缩进级别
            skip_leading: 是否跳过前导空白（用于 -}} 语法）
        """
        if not text:
            return

        # 如果需要跳过前导空白
        if skip_leading:
            text = text.lstrip()

        # 如果处理后为空，不添加代码
        if not text:
            return

        # 使用 repr() 转义字符串，然后通过 exec 输出
        # 避免字符串中包含引号导致语法错误
        escaped = repr(text)
        code_lines.append(' ' * indent + f"_result.append({escaped})")


    def render_to_directory(
        self, target_dir: Path, context: Dict[str, Any]
    ) -> List[str]:
        """将模板渲染到目标目录"""
        created_files = []

        # 处理模板文件
        for template_file in self.get_template_files():
            # 计算相对路径并去掉 .mct 后缀
            rel_path = template_file.relative_to(self.template_dir)
            target_path = target_dir / str(rel_path)[:-3]  # 去掉 .mct

            # 渲染文件名中的变量
            target_path_str = self._render_template(str(target_path), context)
            target_path = Path(target_path_str)

            # 创建目录
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 渲染并写入
            content = self.render_file(template_file, context)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)

            created_files.append(str(target_path.relative_to(target_dir)))

        # 处理静态文件
        for static_file in self.get_static_files():
            rel_path = static_file.relative_to(self.template_dir)
            target_path = target_dir / rel_path

            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 复制文件
            with open(static_file, "rb") as src:
                with open(target_path, "wb") as dst:
                    dst.write(src.read())

            created_files.append(str(rel_path))

        return created_files


