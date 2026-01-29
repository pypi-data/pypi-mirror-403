"""
PDF 压缩功能核心实现
"""

from pathlib import Path

import fitz  # PyMuPDF


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


def compress_pdf(
    input_path: Path, output_path: Path, dpi: int = 150, verbose: bool = False
) -> tuple[int, int]:
    """压缩单个 PDF 文件

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        dpi: 图片重采样 DPI（预留参数，暂未实现）
        verbose: 是否显示详细信息

    Returns:
        (原始大小, 压缩后大小) 字节数
    """
    # TODO: dpi 参数暂未使用，后续可实现真正的图片 DPI 重采样
    if not input_path.exists():
        return 0, 0
        
    original_size = input_path.stat().st_size

    doc = fitz.open(input_path)

    # 统计
    png_count = 0
    jpeg_count = 0
    other_count = 0
    converted_count = 0

    # 遍历处理图片
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]

            try:
                # 提取图片
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue

                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                if image_ext == "png":
                    png_count += 1
                elif image_ext in ("jpeg", "jpg"):
                    jpeg_count += 1
                else:
                    other_count += 1

                # PNG 转 JPEG（仅 >1MB 且无透明通道）
                if image_ext == "png" and len(image_bytes) > 1024 * 1024:
                    # 使用 fitz 的 Pixmap 处理
                    pix = fitz.Pixmap(image_bytes)

                    # 有 alpha 通道则跳过
                    if pix.alpha:
                        pix = None
                        continue

                    # 转为 JPEG
                    new_image = pix.tobytes("jpeg", jpg_quality=85)
                    pix = None

                    # 替换图片
                    page.replace_image(xref, stream=new_image)
                    converted_count += 1

            except Exception as e:
                if verbose:
                    print(f"  ⚠️ 图片处理跳过: {e}")
                continue

    if verbose:
        print(
            f"  📊 图片统计: PNG={png_count}, JPEG={jpeg_count}, 其他={other_count}, 已转换={converted_count}"
        )

    # 清理元数据等
    doc.scrub()

    # 保存（使用 ez_save 自动启用 garbage=3 + deflate）
    doc.ez_save(str(output_path))
    doc.close()

    compressed_size = output_path.stat().st_size
    return original_size, compressed_size
