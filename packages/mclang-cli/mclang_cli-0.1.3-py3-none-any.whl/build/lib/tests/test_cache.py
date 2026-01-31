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
测试 mcli cache 命令
"""

import pytest
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))
from mcli.commands import cache


class TestCacheCommand:
    """cache 命令测试"""

    def test_format_size_bytes(self):
        """测试格式化字节大小"""
        assert cache._format_size(0) == "0.0 B"
        assert cache._format_size(512) == "512.0 B"
        assert cache._format_size(1024) == "1.0 KB"
        assert cache._format_size(1536) == "1.5 KB"
        assert cache._format_size(1024 * 1024) == "1.0 MB"
        assert cache._format_size(1024 * 1024 * 1024) == "1.0 GB"

    def test_format_size_tb(self):
        """测试格式化 TB 大小"""
        assert cache._format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"
        assert cache._format_size(2 * 1024 * 1024 * 1024 * 1024) == "2.0 TB"

    @patch("subprocess.run")
    def test_find_ref_by_hash_found(self, mock_run):
        """测试通过 hash 查找包引用 - 找到匹配"""
        # Mock conan list 命令的返回值
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''{
            "Local Cache": {
                "mclruntime/0.1.7": {
                    "revisions": {
                        "abc123": {
                            "packages": {
                                "c62f50179333d1a2e3f4a5b6c7d8e9f10": {
                                    "info": {}
                                }
                            }
                        }
                    }
                }
            }
        }'''
        mock_run.return_value = mock_result

        result = cache._find_ref_by_hash("c62f50179333")
        assert result == "mclruntime/0.1.7:c62f50179333d1a2e3f4a5b6c7d8e9f10"

    @patch("subprocess.run")
    def test_find_ref_by_hash_not_found(self, mock_run):
        """测试通过 hash 查找包引用 - 未找到匹配"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"Local Cache": {}}'
        mock_run.return_value = mock_result

        result = cache._find_ref_by_hash("notfound")
        assert result is None

    @patch("subprocess.run")
    def test_find_ref_by_hash_case_insensitive(self, mock_run):
        """测试通过 hash 查找包引用 - 不区分大小写"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''{
            "Local Cache": {
                "mclruntime/0.1.7": {
                    "revisions": {
                        "abc123": {
                            "packages": {
                                "C62F50179333": {
                                    "info": {}
                                }
                            }
                        }
                    }
                }
            }
        }'''
        mock_run.return_value = mock_result

        result = cache._find_ref_by_hash("c62f50179333")
        assert result == "mclruntime/0.1.7:C62F50179333"

    def test_is_pattern_match_wildcard_package(self):
        """测试模式匹配 - 通配符包名"""
        assert cache._is_pattern_match("mclruntime/0.1.7", "mcl*", True)
        assert cache._is_pattern_match("mclruntime/0.1.7", "*runtime", True)
        assert not cache._is_pattern_match("gtest/1.14.0", "mcl*", True)

    def test_is_pattern_match_wildcard_full_ref(self):
        """测试模式匹配 - 通配符完整引用"""
        assert cache._is_pattern_match("mclruntime/0.1.7", "mclruntime/*", True)
        assert cache._is_pattern_match("mclruntime/0.1.7", "*/0.1.7", True)
        assert cache._is_pattern_match("mclruntime/0.1.7", "*/*", True)

    def test_is_pattern_match_exact(self):
        """测试模式匹配 - 精确匹配"""
        assert cache._is_pattern_match("mclruntime/0.1.7", "mclruntime", False)
        assert cache._is_pattern_match("mclruntime/0.1.7", "mclruntime/0.1.7", False)
        assert not cache._is_pattern_match("mclruntime/0.1.7", "gtest", False)

    def test_is_pattern_match_prefix(self):
        """测试模式匹配 - 前缀匹配"""
        assert cache._is_pattern_match("mclruntime/0.1.7", "mclruntime/", False)

    @patch("subprocess.run")
    def test_list_matching_packages_empty(self, mock_run):
        """测试列出匹配包 - 空缓存"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"Local Cache": {}}'
        mock_run.return_value = mock_result

        result = cache._list_matching_packages("mcl*")
        assert result is None

    @patch("subprocess.run")
    def test_list_matching_packages_with_wildcard(self, mock_run):
        """测试列出匹配包 - 通配符模式"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''{
            "Local Cache": {
                "mclruntime/0.1.7": {
                    "revisions": {
                        "abc123": {
                            "packages": {
                                "c62f50179333": {
                                    "info": {
                                        "settings": {
                                            "build_type": "Release",
                                            "compiler": "gcc",
                                            "compiler.version": "11"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "gtest/1.14.0": {
                    "revisions": {
                        "def456": {
                            "packages": {
                                "aaa111bbb222": {
                                    "info": {
                                        "settings": {
                                            "build_type": "Debug",
                                            "compiler": "gcc",
                                            "compiler.version": "11"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }'''
        mock_run.return_value = mock_result

        result = cache._list_matching_packages("mcl*")
        assert result is not None
        assert "mclruntime/0.1.7" in result["packages"]
        assert "gtest/1.14.0" not in result["packages"]
        assert result["total_count"] == 1

    @patch("builtins.print")
    def test_print_removal_preview(self, mock_print):
        """测试打印删除预览"""
        matched = {
            "packages": {
                "mclruntime/0.1.7": {
                    "instances": [
                        {
                            "id_short": "c62f50179333",
                            "compiler": "gcc-11",
                            "build_type": "Release"
                        }
                    ]
                }
            },
            "total_count": 1
        }

        cache._print_removal_preview(matched, "mclruntime/0.1.7")

        # 验证打印内容包含关键信息
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = "\n".join(print_calls)
        assert "匹配 'mclruntime/0.1.7' 的包:" in output
        assert "mclruntime/0.1.7" in output
        assert "c62f50179333" in output
        assert "总计: 1 个包实例将被删除" in output

    @patch("subprocess.run")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_cmd_remove_missing_target(self, mock_print, mock_input, mock_run):
        """测试 remove 命令 - 缺少目标参数"""
        args = argparse.Namespace(
            cache_command="remove",
            target=None,
            force=False
        )

        result = cache.cmd_remove(args)
        assert result is False
        # 验证显示错误信息
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = "\n".join(print_calls)
        assert "错误: 请提供要删除的目标" in output

    @patch("builtins.print")
    def test_cmd_remove_hash_not_found(self, mock_print):
        """测试 remove 命令 - hash 未找到（纯 hash 格式）"""
        # 纯 hash 格式（不含 /）但包含 : 的测试
        # 注意：根据当前实现，只有 target 包含 : 且不含 / 时才会调用 _find_ref_by_hash
        # 所以这里测试用包含 : 的格式
        with patch.object(cache, "_find_ref_by_hash", return_value=None):
            args = argparse.Namespace(
                cache_command="remove",
                target="c62f50179333:",  # 添加 : 以触发 hash 查找逻辑
                force=False,
                preview=False
            )

            result = cache.cmd_remove(args)
            assert result is False

            print_calls = [str(call) for call in mock_print.call_args_list]
            output = "\n".join(print_calls)
            assert "未找到" in output

    @patch("subprocess.run")
    @patch("builtins.input", return_value="no")
    @patch("builtins.print")
    def test_cmd_remove_user_cancel(self, mock_print, mock_input, mock_run):
        """测试 remove 命令 - 用户取消"""
        # Mock _list_matching_packages
        with patch("mcli.commands.cache._list_matching_packages") as mock_list:
            mock_list.return_value = {
                "packages": {
                    "mclruntime/0.1.7": {"instances": []}
                },
                "total_count": 1
            }

            args = argparse.Namespace(
                cache_command="remove",
                target="mclruntime/0.1.7",
                force=False
            )

            result = cache.cmd_remove(args)
            assert result is True

            # 验证显示取消信息
            print_calls = [str(call) for call in mock_print.call_args_list]
            output = "\n".join(print_calls)
            assert "操作已取消" in output

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_cmd_remove_preview_mode(self, mock_print, mock_run):
        """测试 remove 命令 - 预览模式"""
        with patch("mcli.commands.cache._list_matching_packages") as mock_list:
            mock_list.return_value = {
                "packages": {
                    "mclruntime/0.1.7": {"instances": []}
                },
                "total_count": 1
            }

            args = argparse.Namespace(
                cache_command="remove",
                target="mcl*",
                force=False,
                preview=True
            )

            result = cache.cmd_remove(args)
            assert result is True

            # 验证不执行实际删除
            mock_run.assert_not_called()

            # 验证显示预览信息
            print_calls = [str(call) for call in mock_print.call_args_list]
            output = "\n".join(print_calls)
            assert "预览模式" in output

    @patch("subprocess.run")
    @patch("builtins.print")
    def test_cmd_remove_wildcard_pattern(self, mock_print, mock_run):
        """测试 remove 命令 - 通配符模式"""
        mock_remove_result = MagicMock()
        mock_remove_result.returncode = 0
        mock_run.return_value = mock_remove_result

        with patch("mcli.commands.cache._list_matching_packages") as mock_list:
            mock_list.return_value = {
                "packages": {
                    "mclruntime/0.1.7": {"instances": []},
                    "mclruntime/0.2.0": {"instances": []}
                },
                "total_count": 2
            }

            args = argparse.Namespace(
                cache_command="remove",
                target="mcl*",
                force=True,
                preview=False
            )

            result = cache.cmd_remove(args)
            assert result is True

            # 验证对每个匹配的引用调用 remove
            assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_run_cache_ls_command(self, mock_run):
        """测试 cache ls 命令"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"Local Cache": {}}'
        mock_run.return_value = mock_result

        args = argparse.Namespace(
            cache_command="ls",
            verbose=False
        )

        result = cache.run_cache(args)
        assert result is True

    def test_run_cache_no_command(self):
        """测试 cache 无子命令"""
        args = argparse.Namespace(cache_command=None)

        with patch("builtins.print") as mock_print:
            result = cache.run_cache(args)
            assert result is True

            # 验证显示帮助信息
            print_calls = [str(call) for call in mock_print.call_args_list]
            output = "\n".join(print_calls)
            assert "用法: mcli cache <command>" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
