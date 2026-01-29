from pathlib import Path

from mark2pdf.core import convert_file


def test_convert_file_output_path_and_call_args(tmp_path, monkeypatch):
    """
    Test that convert_file computes an output path under outdir and passes
    a relative input filename into run_pandoc_typst.
    """
    tmp_path = tmp_path.resolve()

    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    tmp_dir = tmp_path / "tmp"
    in_dir.mkdir()
    out_dir.mkdir()
    tmp_dir.mkdir()

    config_content = """
[paths]
in = "in"
out = "out"
tmp = "tmp"
"""
    (tmp_path / "mark2pdf.config.toml").write_text(config_content)

    input_file = in_dir / "test.md"
    input_file.write_text("# Test\nContent")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("mark2pdf.core.core.check_pandoc_typst", lambda: None)

    captured = {}

    def fake_run_pandoc_typst(
        *,
        input_file,
        output_file,
        template_path,
        pandoc_workdir,
        verbose,
        to_typst,
        **kwargs,
    ):
        captured["input_file"] = input_file
        captured["output_file"] = Path(output_file)
        return True

    monkeypatch.setattr("mark2pdf.core.core.run_pandoc_typst", fake_run_pandoc_typst)
    
    def fake_compress_pdf(input_path, output_path, **kwargs):
        # 模拟压缩：创建输出文件以防止 FileNotFoundError
        # 注意：input_path 在此测试中也不存在，但这无关紧要，因为我们 mock 了 compress_pdf
        output_path.touch()

    monkeypatch.setattr("mark2pdf.core.compress.compress_pdf", fake_compress_pdf)

    result = convert_file(
        input_file="test.md",
        indir=str(in_dir),
        outdir=str(out_dir),
    )

    assert result == captured["output_file"]
    assert captured["input_file"] == "test.md"
    # H1 标题 "# Test" 现在会被用作文件名
    assert captured["output_file"] == out_dir / "Test.pdf"
    assert captured["output_file"].is_absolute()
