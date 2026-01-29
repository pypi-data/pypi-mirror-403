---
name: yakultpdf-workspace
description: 如何在其他项目中建立 yakultpdf 工作区来生成 PDF
---

# yakultpdf 工作区配置指南

在项目中建立独立的 PDF 工作区，使用全局安装的 yakultpdf 生成文档。

## 前置条件

```bash
# 全局安装 yakultpdf
uv tool install yakultpdf
# 或: pipx install yakultpdf

# 依赖: Pandoc + Typst
```

---

## 1. 初始化工作区

> [!IMPORTANT]
> **工作区目录由用户自定义**，不建议放在项目根目录。

```bash
# 示例：在项目中创建 docs-pdf 目录
mkdir docs-pdf && cd docs-pdf
yakultpdf init .
```

生成结构：
```
docs-pdf/
├── mark2pdf.config.toml   # 配置
├── frontmatter.yaml       # 默认元数据
├── createpdf.py           # 自定义预处理脚本
├── in/                    # 输入目录
│   └── images/
├── out/                   # 输出目录
└── template/              # 本地模板（可选）
```

---

## 2. 配置文件

`mark2pdf.config.toml`：
```toml
project_name = "my-docs"

[paths]
in = "in"
out = "out"

[options]
default_template = "nb.typ"
```

---

## 3. 自定义预处理 (createpdf.py)

> [!TIP]
> 需要对 Markdown 做前置处理时，编辑 `createpdf.py` 中的 `preprocess()` 函数。

```python
def preprocess(content: str) -> str:
    # 替换特殊语法、敏感词等
    content = content.replace("敏感词", "***")
    return content
```

运行：`./createpdf.py sample.md`

---

## 4. 常用命令

```bash
cd docs-pdf

yakultpdf convert in/文档.md          # 转换单文件
yakultpdf convert --dir in/章节/      # 合并转换目录
yakultpdf convert in/文档.md -v       # 详细输出
yakultpdf template                    # 导出内置模板
yakultpdf fonts install lxgw-wenkai   # 安装字体
```

---

## 5. Frontmatter 示例

```yaml
---
title: "文档标题"
author: "作者"
toc-depth: 3
theme:
  template: "nb"
  coverstyle: "darkbg"
---
```

---


## 参考文档

`docs/` 目录下的详细文档：
- **工作区使用指南** - 完整配置与高级用法
- **配置指南** - frontmatter 全部配置项
- **CLI使用说明** - 所有命令参考
- **nb-syntax** - 模板扩展语法（fullimage、topimage 等）
