from unittest.mock import MagicMock, patch

import pytest

from mark2pdf.helper_typst import run_pandoc_typst


class TestRunPandocTypst:
    """测试 run_pandoc_typst 函数"""

    @pytest.fixture
    def mock_subprocess(self):
        with patch("mark2pdf.helper_typst.helper_typst.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            yield mock_run

    def test_single_file_template(self, tmp_path, mock_subprocess):
        """测试单文件模板处理：card.typ"""
        workdir = tmp_path / "work"
        workdir.mkdir()

        input_file = workdir / "test.md"
        input_file.write_text("# Test")
        output_file = workdir / "test.pdf"

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "card.typ"
        template_file.write_text("# Template")

        # 在 pandoc 执行时检查模板文件是否已复制到工作目录
        def side_effect(*args, **kwargs):
            # 检查模板文件是否在工作目录中
            expected_template = workdir / "card.typ"
            assert expected_template.exists(), "模板文件未复制到工作目录"
            # 创建输出文件
            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        result = run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            verbose=True,
        )

        assert result is True

        # 验证模板文件在转换后被清理
        target_template = workdir / "card.typ"
        assert not target_template.exists(), "模板文件未被清理"

    def test_directory_template(self, tmp_path, mock_subprocess):
        """测试目录式模板处理：nb/nb.typ"""
        workdir = tmp_path / "work"
        workdir.mkdir()

        input_file = workdir / "test.md"
        input_file.write_text("# Test")
        output_file = workdir / "test.pdf"

        template_root = tmp_path / "templates"
        template_dir = template_root / "nb"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "nb.typ"
        template_file.write_text("# Template")
        lib_file = template_dir / "lib.typ"  # 模拟依赖文件
        lib_file.write_text("# Lib")

        # 在 pandoc 执行时检查模板目录内容是否已平铺复制
        def side_effect(*args, **kwargs):
            # 验证 nb.typ 和 lib.typ 都在工作目录根目录下
            assert (workdir / "nb.typ").exists(), "模板文件未平铺复制"
            assert (workdir / "lib.typ").exists(), "依赖文件未平铺复制"

            # 验证没有 nb 子目录
            assert not (workdir / "nb").exists(), "不应创建子目录"

            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        # 使用真实的 copytree/copy2，不需要 patch 它们，因为我们在验证副作用
        # 只需要 patch subprocess.run

        result = run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            verbose=True,
        )

        assert result is True

        # 验证清理
        assert not (workdir / "nb.typ").exists(), "模板文件未被清理"
        assert not (workdir / "lib.typ").exists(), "依赖文件未被清理"

    def test_extra_arguments(self, tmp_path, mock_subprocess):
        """测试额外参数传递"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Template")
        input_file = workdir / "test.md"
        output_file = workdir / "test.pdf"

        # 模拟 pandoc 生成输出文件
        # 使用 lambda 时要小心，因为它不接受语句。
        def side_effect(*args, **kwargs):
            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        result = run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            verbose=False,
            with_pagenumber=True,
            cover_image="cover.jpg",
        )

        assert result is True

    def test_output_typst(self, tmp_path, mock_subprocess):
        """测试输出 typst 格式"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Tpl")

        input_file = workdir / "in.md"
        output_file = workdir / "out.pdf"

        def side_effect(*args, **kwargs):
            # 确保实际期望的是 .typ 文件
            real_output = output_file.with_suffix(".typ")
            real_output.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        result = run_pandoc_typst(
            str(input_file), str(output_file), str(template_file), str(workdir), to_typst=True
        )

        assert result is True
        assert output_file.with_suffix(".typ").exists()


class TestDirectoryTemplateEdgeCases:
    """测试目录式模板的边界情况"""

    @pytest.fixture
    def mock_subprocess(self):
        with patch("mark2pdf.helper_typst.helper_typst.subprocess.run") as mock_run:
            yield mock_run

    def test_directory_template_with_subdirectory(self, tmp_path, mock_subprocess):
        """测试目录式模板包含子目录（如 images/）"""
        workdir = tmp_path / "work"
        workdir.mkdir()

        input_file = workdir / "test.md"
        input_file.write_text("# Test")
        output_file = workdir / "test.pdf"

        # 创建目录式模板，包含一个子目录
        template_root = tmp_path / "templates"
        template_dir = template_root / "nb"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "nb.typ"
        template_file.write_text("# Template")

        # 创建 images 子目录和内容
        images_dir = template_dir / "images"
        images_dir.mkdir()
        (images_dir / "logo.png").write_bytes(b"fake image")

        def side_effect(*args, **kwargs):
            # 验证子目录被复制
            assert (workdir / "images").exists(), "子目录未复制"
            assert (workdir / "images" / "logo.png").exists(), "子目录中的文件未复制"
            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        result = run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            verbose=True,
        )

        assert result is True

    def test_hidden_files_skipped(self, tmp_path, mock_subprocess):
        """测试隐藏文件（以.开头）不被复制"""
        workdir = tmp_path / "work"
        workdir.mkdir()

        input_file = workdir / "test.md"
        input_file.write_text("# Test")
        output_file = workdir / "test.pdf"

        template_root = tmp_path / "templates"
        template_dir = template_root / "nb"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "nb.typ"
        template_file.write_text("# Template")

        # 创建隐藏文件
        (template_dir / ".gitignore").write_text("*.log")
        (template_dir / ".DS_Store").write_bytes(b"hidden")

        def side_effect(*args, **kwargs):
            # 验证隐藏文件未被复制
            assert not (workdir / ".gitignore").exists(), "隐藏文件不应被复制"
            assert not (workdir / ".DS_Store").exists(), "隐藏文件不应被复制"
            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        result = run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            verbose=True,
        )

        assert result is True


class TestCommandBuilding:
    """测试命令构建逻辑"""

    @pytest.fixture
    def mock_subprocess(self):
        with patch("mark2pdf.helper_typst.helper_typst.subprocess.run") as mock_run:
            yield mock_run

    def test_command_includes_template(self, tmp_path, mock_subprocess):
        """测试命令包含正确的模板参数"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Template")
        input_file = workdir / "test.md"
        output_file = workdir / "test.pdf"

        captured_cmd = []

        def side_effect(cmd, *args, **kwargs):
            captured_cmd.extend(cmd)
            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
        )

        # 验证命令
        assert "pandoc" in captured_cmd
        assert "--template=card.typ" in captured_cmd
        assert "--pdf-engine=typst" in captured_cmd
        assert "--wrap=none" in captured_cmd

    def test_kwargs_converted_to_variables(self, tmp_path, mock_subprocess):
        """测试 kwargs 参数转换为 pandoc -V 参数"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Template")
        input_file = workdir / "test.md"
        output_file = workdir / "test.pdf"

        captured_cmd = []

        def side_effect(cmd, *args, **kwargs):
            captured_cmd.extend(cmd)
            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            with_pagenumber=True,
            cover_image="cover.jpg",
        )

        # 验证参数转换：下划线变连字符，布尔值变小写
        assert "-V" in captured_cmd
        assert "with-pagenumber=true" in captured_cmd
        assert "cover-image=cover.jpg" in captured_cmd

    def test_font_paths_added(self, tmp_path, mock_subprocess):
        """测试字体路径被正确添加"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Template")
        input_file = workdir / "test.md"
        output_file = workdir / "test.pdf"

        # 创建字体目录
        font_dir = tmp_path / "fonts"
        font_dir.mkdir()

        captured_cmd = []

        def side_effect(cmd, *args, **kwargs):
            captured_cmd.extend(cmd)
            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            font_paths=[str(font_dir)],
        )

        # 验证字体路径参数
        assert "--pdf-engine-opt" in captured_cmd
        font_opt_idx = captured_cmd.index("--pdf-engine-opt")
        assert f"--font-path={font_dir}" in captured_cmd[font_opt_idx + 1]


class TestExecutionFailure:
    """测试执行失败的情况"""

    @pytest.fixture
    def mock_subprocess(self):
        with patch("mark2pdf.helper_typst.helper_typst.subprocess.run") as mock_run:
            yield mock_run

    def test_pandoc_returns_nonzero(self, tmp_path, mock_subprocess):
        """测试 pandoc 返回非零退出码"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Template")
        input_file = workdir / "test.md"
        output_file = workdir / "test.pdf"

        mock_subprocess.return_value = MagicMock(returncode=1, stderr="Error!")

        result = run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            verbose=True,
        )

        assert result is False

    def test_output_file_not_created(self, tmp_path, mock_subprocess):
        """测试 pandoc 成功但输出文件未生成"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Template")
        input_file = workdir / "test.md"
        output_file = workdir / "test.pdf"

        # pandoc 返回0但不创建文件
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            verbose=True,
        )

        assert result is False


class TestCleanupBehavior:
    """测试清理行为"""

    @pytest.fixture
    def mock_subprocess(self):
        with patch("mark2pdf.helper_typst.helper_typst.subprocess.run") as mock_run:
            yield mock_run

    def test_no_cleanup_on_failure(self, tmp_path, mock_subprocess):
        """测试失败时模板文件不被清理（便于调试）"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Template")
        input_file = workdir / "test.md"
        output_file = workdir / "test.pdf"

        # pandoc 失败
        mock_subprocess.return_value = MagicMock(returncode=1, stderr="Error!")

        run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
        )

        # 失败时模板文件应该保留（当前实现是失败时直接返回，不清理）
        # 验证这个行为
        target_template = workdir / "card.typ"
        assert target_template.exists(), "失败时模板文件应保留便于调试"

    def test_cleanup_on_success(self, tmp_path, mock_subprocess):
        """测试成功时模板文件被清理"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Template")
        input_file = workdir / "test.md"
        output_file = workdir / "test.pdf"

        def side_effect(*args, **kwargs):
            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
        )

        target_template = workdir / "card.typ"
        assert not target_template.exists(), "成功时模板文件应被清理"


class TestListArgumentsHandling:
    """测试列表参数处理（用于 disables 等多值参数）"""

    @pytest.fixture
    def mock_subprocess(self):
        with patch("mark2pdf.helper_typst.helper_typst.subprocess.run") as mock_run:
            yield mock_run

    def test_list_values_expanded_to_multiple_v_args(self, tmp_path, mock_subprocess):
        """测试列表值被展开为多个 -V 参数"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Template")
        input_file = workdir / "test.md"
        output_file = workdir / "test.pdf"

        captured_cmd = []

        def side_effect(cmd, *args, **kwargs):
            captured_cmd.extend(cmd)
            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            disables=["cover", "toc"],
        )

        # 验证列表被展开为多个 -V 参数
        # 预期: -V disables=cover -V disables=toc
        v_indices = [i for i, x in enumerate(captured_cmd) if x == "-V"]
        values_after_v = [captured_cmd[i + 1] for i in v_indices if i + 1 < len(captured_cmd)]

        assert "disables=cover" in values_after_v, f"Expected 'disables=cover' in {values_after_v}"
        assert "disables=toc" in values_after_v, f"Expected 'disables=toc' in {values_after_v}"

    def test_empty_list_produces_no_args(self, tmp_path, mock_subprocess):
        """测试空列表不产生参数"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Template")
        input_file = workdir / "test.md"
        output_file = workdir / "test.pdf"

        captured_cmd = []

        def side_effect(cmd, *args, **kwargs):
            captured_cmd.extend(cmd)
            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            disables=[],
        )

        # 空列表不应产生任何 disables 参数
        v_indices = [i for i, x in enumerate(captured_cmd) if x == "-V"]
        values_after_v = [captured_cmd[i + 1] for i in v_indices if i + 1 < len(captured_cmd)]

        disables_values = [v for v in values_after_v if v.startswith("disables=")]
        assert len(disables_values) == 0, f"Empty list should produce no args, got {disables_values}"

    def test_tuple_values_also_expanded(self, tmp_path, mock_subprocess):
        """测试元组值也被正确展开"""
        workdir = tmp_path / "work"
        workdir.mkdir()
        template_file = tmp_path / "card.typ"
        template_file.write_text("# Template")
        input_file = workdir / "test.md"
        output_file = workdir / "test.pdf"

        captured_cmd = []

        def side_effect(cmd, *args, **kwargs):
            captured_cmd.extend(cmd)
            output_file.touch()
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = side_effect

        run_pandoc_typst(
            str(input_file),
            str(output_file),
            str(template_file),
            str(workdir),
            disables=("cover", "backcover"),
        )

        v_indices = [i for i, x in enumerate(captured_cmd) if x == "-V"]
        values_after_v = [captured_cmd[i + 1] for i in v_indices if i + 1 < len(captured_cmd)]

        assert "disables=cover" in values_after_v
        assert "disables=backcover" in values_after_v
