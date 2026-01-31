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
测试模板引擎
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from mcli.template import ProjectTemplate


class TestTemplateEngine:
    """模板引擎测试"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.template = ProjectTemplate(Path(__file__).parent.parent / "templates")

    def test_plain_text(self):
        """测试纯文本输出"""
        template = "Hello, World!"
        result = self.template._render_template(template, {})
        assert result == "Hello, World!"

    def test_variable_substitution(self):
        """测试变量替换 {{ var }}"""
        template = "Hello, {{ name }}!"
        result = self.template._render_template(template, {"name": "Alice"})
        assert result == "Hello, Alice!"

    def test_multiple_variables(self):
        """测试多个变量"""
        template = "{{ a }} + {{ b }} = {{ c }}"
        result = self.template._render_template(template, {"a": 1, "b": 2, "c": 3})
        assert result == "1 + 2 = 3"

    def test_for_loop(self):
        """测试 for 循环"""
        template = """Items:
{% for item in items %}
{{- f"- {item}" }}
{% endfor -%}
Done"""
        result = self.template._render_template(template, {"items": ["apple", "banana", "cherry"]})
        assert result == """Items:
- apple
- banana
- cherry
Done"""

    def test_for_loop_with_dict(self):
        """测试 for 循环遍历字典"""
        template = """
{% for key, value in data.items() %}
{{- key }}: {{ value }}
{% endfor -%}
"""
        result = self.template._render_template(template, {"data": {"a": 1, "b": 2}})
        assert result == """
a: 1
b: 2
"""

    def test_if_condition_true(self):
        """测试 if 条件为真"""
        template = """{% if show %}
Visible
{% endif %}"""
        result = self.template._render_template(template, {"show": True})
        expected = """
Visible
"""
        assert result == expected

    def test_if_condition_false(self):
        """测试 if 条件为假"""
        template = """{% if show %}
Visible
{% endif %}"""
        result = self.template._render_template(template, {"show": False})
        expected = ""

        assert result == expected

    def test_if_else(self):
        """测试 if-else"""
        template = """{% if value %}
Yes
{% else %}
No
{% endif %}"""
        result_true = self.template._render_template(template, {"value": True})
        result_false = self.template._render_template(template, {"value": False})
        expected_true = """
Yes
"""
        expected_false = """
No
"""
        assert result_true == expected_true
        assert result_false == expected_false

    def test_single_brace(self):
        """测试单个大括号不转义"""
        template = "options = {test: True}"
        result = self.template._render_template(template, {})
        assert result == "options = {test: True}"

    def test_f_string_like_syntax(self):
        """测试类似 f-string 的语法"""
        template = 'cmake_content.append(f"set({{ cmake_var }})")'
        result = self.template._render_template(template, {"cmake_var": "SOURCES"})
        assert result == 'cmake_content.append(f"set(SOURCES)")'

    def test_string_inside_code_block(self):
        template = '''{% for item in items %}
print("hello {{item}}")
{%- endfor %}
'''
        result = self.template._render_template(template, {"items": [1, 2]})
        assert result == """
print("hello 1")
print("hello 2")
"""

    def test_nested_loops(self):
        """测试嵌套循环"""
        template = """
{%- for row in matrix %}
    {%- for col in row %}
{{ col }}
    {%- endfor %}
{%- endfor %}
"""
        result = self.template._render_template(template, {"matrix": [[1, 2], [3, 4]]})
        assert result == """
1
2
3
4
"""

    def test_empty_loop(self):
        """测试空列表循环"""
        template = """{% for item in items %}
{{ item }}
{% endfor %}
Done"""
        result = self.template._render_template(template, {"items": []})
        assert result == """
Done"""

    def test_newline_preservation(self):
        """测试换行符保留"""
        template = "Line 1\nLine 2\nLine 3"
        result = self.template._render_template(template, {})
        assert result == "Line 1\nLine 2\nLine 3"

    def test_python_code_generation(self):
        """测试生成 Python 代码"""
        template = """PROJECT_VERSION = "{{ version }}"
CONAN_REQUIRES = [
{% for req in requires %}
    "{{ req }}",
{% endfor %}
]"""
        result = self.template._render_template(template, {
            "version": "0.3.0",
            "requires": ["mclruntime/[~0.1.0]", "gtest/[~1.14.0]"]
        })
        expected = '''PROJECT_VERSION = "0.3.0"
CONAN_REQUIRES = [

    "mclruntime/[~0.1.0]",

    "gtest/[~1.14.0]",

]'''
        assert result == expected

    def test_dict_literal(self):
        """测试字典字面量"""
        template = """options = {
    "test": True,
    "asan": False,
}"""
        result = self.template._render_template(template, {})
        expected = """options = {
    "test": True,
    "asan": False,
}"""
        assert result == expected

    def test_multiline_string_in_code(self):
        """测试代码块中的多行字符串"""
        template = '''{% if condition %}
code_block.append("""
    This is a multiline string
    with {{ content }} inside
""")
{% endif %}'''
        result = self.template._render_template(template, {
            "condition": True,
            "content": "value"
        })
        expected = '''
code_block.append("""
    This is a multiline string
    with value inside
""")
'''
        assert result == expected

    def test_escape_sequences(self):
        """测试转义序列"""
        template = r'path = "C:\\Users\\test"'
        result = self.template._render_template(template, {})
        assert result == r'path = "C:\\Users\\test"'

    def test_complex_template(self):
        """测试复杂模板：结合循环、条件、变量"""
        template = """# Configuration
{% if debug %}
DEBUG = True
{% endif %}
Version: {{ version }}
Dependencies:
{% for dep in dependencies %}
- {{ dep["name"] }} ({{ dep["version"] }})
{% endfor %}"""
        result = self.template._render_template(template, {
            "debug": True,
            "version": "1.0.0",
            "dependencies": [
                {"name": "mclruntime", "version": "0.1.0"},
                {"name": "gtest", "version": "1.14.0"}
            ]
        })
        expected = """# Configuration

DEBUG = True

Version: 1.0.0
Dependencies:

- mclruntime (0.1.0)

- gtest (1.14.0)
"""
        assert result == expected

    def test_expr_with_spaces(self):
        """测试表达式中的空格"""
        template = "Value: {{  1 + 2  }}"
        result = self.template._render_template(template, {})
        assert result == "Value: 3"

    def test_empty_template(self):
        """测试空模板"""
        result = self.template._render_template("", {})
        assert result == ""

    def test_template_with_only_newlines(self):
        """测试只有换行符的模板"""
        template = "\n\n\n"
        result = self.template._render_template(template, {})
        assert result == "\n\n\n"

    def test_trim_leading_whitespace_with_dash_percent(self):
        """测试 {%- 去除前面的空白"""
        template = """Hello
{%- if show %}Visible{%- endif %}"""
        result = self.template._render_template(template, {"show": True})
        # {%- 去除前面的空白
        assert result == "HelloVisible"

    def test_trim_trailing_whitespace_with_percent_dash(self):
        """测试 -%} 去除后面的空白"""
        template = """Hello {% if show -%}
 {{ name -}}
{% endif -%} World"""
        result = self.template._render_template(template, {"show": True, "name": "Alice"})
        # -%} 去除后面的空白
        assert result == "Hello AliceWorld"

    def test_trim_both_sides(self):
        """测试 {%- ... -%} 去除两边的空白"""
        template = """Hello
{%- if show -%}
Visible
{%- endif -%}
World"""
        result = self.template._render_template(template, {"show": True})
        # {%- 去除前面的空白，-%} 去除后面的空白
        assert result == "HelloVisibleWorld"

    def test_trim_leading_with_expr_dash(self):
        """测试 {{- 去除前面的空白"""
        template = """Hello
{{- name -}}
World"""
        result = self.template._render_template(template, {"name": "Alice"})
        assert result == "HelloAliceWorld"

    def test_trim_trailing_with_expr_dash(self):
        """测试 -}} 去除后面的空白"""
        template = """Hello {{ name -}}
World"""
        result = self.template._render_template(template, {"name": "Bob"})
        assert result == "Hello BobWorld"

    def test_trim_in_loop(self):
        """测试循环中的空白控制"""
        template = """[
{% for item in items -%}
    {{ item }},
{%- endfor %}
]"""
        result = self.template._render_template(template, {"items": ["a", "b", "c"]})
        # -%} 去除后面的空白
        assert result == "[\na,b,c,\n]"

    def test_trim_removes_spaces_and_tabs(self):
        """测试空白控制去除空格和制表符"""
        template = "Hello \t {{- name -}} \t World"
        result = self.template._render_template(template, {"name": "X"})
        # {{- 去除前面的空格和制表符，-}} 去除后面的
        assert result == "HelloXWorld"

    def test_no_trim_without_dash(self):
        """测试不使用 dash 时保留空白"""
        template = """Hello
{% if show %}
Visible
{% endif %}
World"""
        result = self.template._render_template(template, {"show": True})
        # 没有 dash 时应该保留换行符（包括模板中的换行）
        assert result == "Hello\n\nVisible\n\nWorld"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
