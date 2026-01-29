"""
Typst 辅助模块

提供 Typst 相关的处理功能，包括模板依赖解析、路径解析等。
参考 mark2pdf.helper_workingpath 和 mark2pdf.helper_markdown 的设计模式。
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

_TOOL_CHECKED = False
_SKIP_TOOL_CHECK = False

# 已废弃的函数：parse_template_deps, parse_template_assets, copy_template_deps, cleanup_template_deps
# 现在使用目录式模板简化逻辑，直接复制整个目录。


def set_tool_check_skip(skip: bool) -> None:
    global _SKIP_TOOL_CHECK
    _SKIP_TOOL_CHECK = bool(skip)


def _copy_template_to_workdir(
    template_path: str | Path,
    workdir_path: Path,
    verbose: bool = False,
) -> tuple[str, list[Path]]:
    """
    复制模板文件到工作目录

    Args:
        template_path: 原始模板路径
        workdir_path: 工作目录路径
        verbose: 是否显示详细信息

    Returns:
        (模板文件名, 需要清理的文件/目录列表)
    """
    template_file = Path(template_path)
    cleanup_items: list[Path] = []

    # 判断是否为目录式模板（模板文件在子目录中，如 nb/nb.typ）
    is_dir_template = template_file.parent.name == template_file.stem

    if is_dir_template:
        template_dir = template_file.parent
        template_filename = template_file.name

        if verbose:
            print(f"目录式模板：{template_path}")
            print(f"平铺复制模板目录内容：{template_dir.name}/ -> ./")

        for item in template_dir.iterdir():
            if item.name.startswith("."):  # 跳过隐藏文件
                continue

            dst = workdir_path / item.name

            if item.is_dir():
                if dst.exists() and dst.is_dir():
                    shutil.copytree(item, dst, dirs_exist_ok=True)
                elif not dst.exists():
                    shutil.copytree(item, dst)
                    cleanup_items.append(dst)
                else:
                    if verbose:
                        print(f"  ⚠️ 跳过复制目录（目标已存在文件）：{item.name}")
            else:
                shutil.copy2(item, dst)
                cleanup_items.append(dst)
    else:
        template_filename = template_file.name
        if verbose:
            print(f"单文件模板：{template_path}")

        target_template = workdir_path / template_filename
        shutil.copy2(template_file, target_template)
        cleanup_items.append(target_template)

    if verbose:
        print(f"使用模板文件：{template_filename}")

    return template_filename, cleanup_items


def _build_pandoc_command(
    input_file: str,
    output_file: str | Path,
    template_filename: str,
    font_paths: list[str] | None,
    pandoc_workdir: str,
    verbose: bool,
    extra_args: dict,
) -> list[str]:
    """
    构建 pandoc 命令

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        template_filename: 模板文件名（在工作目录中）
        font_paths: 字体路径列表
        pandoc_workdir: pandoc 工作目录
        verbose: 是否显示详细信息
        extra_args: 额外参数 (kwargs)

    Returns:
        命令列表
    """
    cmd = [
        "pandoc",
        input_file,
        f"--template={template_filename}",
        "--pdf-engine=typst",
        "--wrap=none",
        "-o",
        str(output_file),
    ]

    _add_font_paths(cmd, font_paths, pandoc_workdir, verbose)
    _add_pandoc_arguments(cmd, extra_args)

    return cmd


def _execute_pandoc(
    cmd: list[str],
    pandoc_workdir: str,
    output_file: str | Path,
    verbose: bool,
) -> bool:
    """
    执行 pandoc 命令并验证结果

    Args:
        cmd: pandoc 命令列表
        pandoc_workdir: 工作目录
        output_file: 期望的输出文件路径
        verbose: 是否显示详细信息

    Returns:
        是否成功
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=pandoc_workdir,
        )

        if result.returncode != 0:
            if verbose:
                print(f"pandoc 执行失败：{result.stderr}")
            return False

        if not Path(output_file).exists():
            if verbose:
                print(f"输出文件未能生成：{output_file}")
            return False

        return True

    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"pandoc 执行失败：{e}")
            if e.stderr:
                print(f"错误信息：{e.stderr}")
        return False
    except Exception as e:
        if verbose:
            print(f"转换过程中出错：{e}")
        return False


def _cleanup_template_files(cleanup_items: list[Path], verbose: bool = False) -> None:
    """
    清理临时模板文件

    Args:
        cleanup_items: 需要清理的文件/目录列表
        verbose: 是否显示详细信息
    """
    for item in cleanup_items:
        try:
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            elif item.exists():
                item.unlink()
        except Exception:
            pass

    if verbose:
        print("  ✓ 清理临时模板文件")


def run_pandoc_typst(
    input_file: str,
    output_file: str,
    template_path: str,
    pandoc_workdir: str,
    verbose: bool = False,
    to_typst: bool = False,
    font_paths: list[str] | None = None,
    **kwargs,
) -> bool:
    """
    运行 pandoc 命令将 markdown 转换为 PDF 或 typst

    Args:
        input_file: 输入文件路径（相对于 pandoc_workdir）
        output_file: 输出文件路径（建议使用绝对路径）
        template_path: 模板文件路径
        pandoc_workdir: pandoc 工作目录
        verbose: 是否显示详细信息
        to_typst: 是否输出 typst 文件而不是 PDF
        font_paths: 额外字体目录列表
        **kwargs: 额外的 pandoc 变量参数

    Returns:
        转换是否成功
    """
    # 1. 处理输出文件扩展名
    if to_typst:
        output_file = Path(output_file).with_suffix(".typ")

    workdir_path = Path(pandoc_workdir)

    # 2. 复制模板到工作目录
    template_filename, cleanup_items = _copy_template_to_workdir(
        template_path, workdir_path, verbose
    )

    # 3. 构建命令
    cmd = _build_pandoc_command(
        input_file, output_file, template_filename,
        font_paths, pandoc_workdir, verbose, kwargs
    )

    # 4. 执行
    success = _execute_pandoc(cmd, pandoc_workdir, output_file, verbose)

    # 5. 清理（仅在成功时）
    if success:
        _cleanup_template_files(cleanup_items, verbose)
        try:
            rel_output = os.path.relpath(output_file)
        except ValueError:
            rel_output = output_file
        print(f"⚡️ 转换成功：{rel_output}")

    return success


def _add_pandoc_arguments(cmd: list, kwargs: dict):
    """
    根据 kwargs 参数添加 pandoc 命令行参数

    Args:
        cmd (list): 要修改的命令列表
        kwargs (dict): 额外的参数

    支持的值类型：
        - 布尔值：转换为小写字符串 (true/false)
        - 列表/元组：展开为多个 -V key=item 参数
        - 其他：直接转换为字符串
    """
    for key, value in kwargs.items():
        if value is None:
            continue

        var_name = key.replace("_", "-")

        # 处理列表/元组：展开为多个 -V 参数
        if isinstance(value, list | tuple):
            for item in value:
                if item is not None:
                    cmd.extend(["-V", f"{var_name}={item}"])
        # 处理布尔值
        elif isinstance(value, bool):
            cmd.extend(["-V", f"{var_name}={str(value).lower()}"])
        # 处理其他值
        else:
            cmd.extend(["-V", f"{var_name}={value}"])


def _add_font_paths(
    cmd: list,
    font_paths: list[str] | tuple[str, ...] | str | None,
    base_dir: str | Path,
    verbose: bool = False,
) -> None:
    """
    为 pandoc 命令添加 Typst 字体路径

    Args:
        cmd (list): 要修改的命令列表
        font_paths: 字体路径列表或单个路径
        base_dir: 相对路径的基准目录（pandoc 工作目录）
        verbose (bool): 是否显示详细信息
    """
    if not font_paths:
        return

    if isinstance(font_paths, str | Path):
        font_paths = [str(font_paths)]

    base_path = Path(base_dir)
    seen = set()

    for font_path in font_paths:
        if not font_path:
            continue
        expanded = os.path.expandvars(str(font_path))
        candidate = Path(expanded).expanduser()
        if not candidate.is_absolute():
            candidate = base_path / candidate
        candidate_str = str(candidate)
        if candidate_str in seen:
            continue
        if not candidate.exists():
            if verbose:
                print(f"  ⚠️ 字体目录不存在，已跳过: {candidate_str}")
            continue
        if not candidate.is_dir():
            if verbose:
                print(f"  ⚠️ 字体路径不是目录，已跳过: {candidate_str}")
            continue
        cmd.extend(["--pdf-engine-opt", f"--font-path={candidate_str}"])
        seen.add(candidate_str)


def check_pandoc_typst(skip: bool | None = None):
    """
    检查 pandoc 和 typst 是否已安装

    Raises:
        SystemExit: 如果任一工具未安装
    """
    global _TOOL_CHECKED
    if skip is None:
        skip = _SKIP_TOOL_CHECK
    if skip or _TOOL_CHECKED:
        return

    try:
        subprocess.run(["pandoc", "--version"], capture_output=True, text=True)
    except FileNotFoundError:
        print("错误：pandoc 未安装或不在 PATH 中，请先安装 pandoc")
        sys.exit(1)

    try:
        subprocess.run(["typst", "--version"], capture_output=True, text=True)
    except FileNotFoundError:
        print("错误：typst 未安装或不在 PATH 中，请先安装 typst")
        sys.exit(1)

    _TOOL_CHECKED = True
