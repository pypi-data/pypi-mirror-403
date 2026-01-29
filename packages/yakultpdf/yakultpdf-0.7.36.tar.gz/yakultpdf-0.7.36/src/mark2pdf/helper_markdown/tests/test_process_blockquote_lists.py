"""测试 _process_blockquote_lists 函数"""

import pytest

from mark2pdf.helper_markdown.md_preprocess import _process_blockquote_lists


class TestProcessBlockquoteLists:
    """测试引用块内列表处理"""

    def test_basic_unordered_list(self):
        """测试基本无序列表"""
        input_text = """> 一些前提假设：
> - 项目1
> - 项目2
> - 项目3"""
        
        expected = """> 一些前提假设：
>
> - 项目1
>
> - 项目2
>
> - 项目3"""
        
        result = _process_blockquote_lists(input_text)
        assert result == expected

    def test_ordered_list(self):
        """测试有序列表"""
        input_text = """> 步骤：
> 1. 第一步
> 2. 第二步"""
        
        expected = """> 步骤：
>
> 1. 第一步
>
> 2. 第二步"""
        
        result = _process_blockquote_lists(input_text)
        assert result == expected

    def test_mixed_content(self):
        """测试混合内容（列表和非列表）"""
        input_text = """> 前言
> 这是普通文本
> - 列表项1
> - 列表项2
> 结尾文字"""
        
        expected = """> 前言
> 这是普通文本
>
> - 列表项1
>
> - 列表项2
> 结尾文字"""
        
        result = _process_blockquote_lists(input_text)
        assert result == expected

    def test_non_blockquote_list(self):
        """测试非引用块列表不受影响"""
        input_text = """普通段落
- 列表项1
- 列表项2"""
        
        # 非引用块列表不应被处理
        result = _process_blockquote_lists(input_text)
        assert result == input_text

    def test_empty_quote_line_preserved(self):
        """测试已有空引用行不重复添加"""
        input_text = """> 标题
>
> - 项目1
> - 项目2"""
        
        expected = """> 标题
>
> - 项目1
>
> - 项目2"""
        
        result = _process_blockquote_lists(input_text)
        assert result == expected

    def test_asterisk_list(self):
        """测试星号列表"""
        input_text = """> 注意事项：
> * 项目A
> * 项目B"""
        
        expected = """> 注意事项：
>
> * 项目A
>
> * 项目B"""
        
        result = _process_blockquote_lists(input_text)
        assert result == expected

    def test_plus_list(self):
        """测试加号列表"""
        input_text = """> 要点：
> + 要点1
> + 要点2"""
        
        expected = """> 要点：
>
> + 要点1
>
> + 要点2"""
        
        result = _process_blockquote_lists(input_text)
        assert result == expected
