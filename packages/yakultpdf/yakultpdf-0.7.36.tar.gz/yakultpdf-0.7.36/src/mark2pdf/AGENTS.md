# mark2pdf 核心源码指南

## 模块概览

本目录包含 `yakultpdf` 的核心逻辑：

- **`cli.py`**: 命令行入口 (Typer app)。
- **`conversion.py`**: 转换流程的主控制器。
  - 负责协调 Markdown 解析 -> Typst 生成 -> PDF 编译。
- **`defaults.py`**: 默认配置常量。
- **`process_builder.py`**: 外部命令 (pandoc, typst) 构建器。

## 子模块功能

| 模块 | 功能说明 |
| :--- | :--- |
| **`helper_markdown/`** | Markdown 解析与预处理。提取 frontmatter, 处理 TOC。 |
| **`helper_typst/`** | 将中间数据转换为 `.typ` 文件。 |
| **`helper_mdimage/`** | 图片路径处理和优化。 |
| **`templates/`** | 模版管理系统 (Jinja2)。 |
| **`config/`** | 配置加载 (TOML + ENV)。 |

## 开发指引

- **新增功能**: 通常需要在 `conversion.py` 中添加流程步骤，并在对应的 `helper_*` 中实现逻辑。
- **CLI 命令**: 在 `commands/` 目录下新增命令文件，并在 `cli.py` 中注册。
