# 模版系统指南

## 概述
YakultPDF 原生支持 **Pandoc** 的 Typst 模版引擎。

- **机制**: Markdown 内容由 Pandoc 转换为 Typst 格式，并注入到模版中的 `$body$` 占位符。
- **模版语言**: 使用 Pandoc 模版语法 (如 `$if(title)$`, `$body$`, `$for(author)$`)。

## 核心模版：NB 
`nb` 是最常用、功能最全的模版系列，位于 `src/mark2pdf/templates/nb/`。

### 结构与模块
- **`nb.typ`**: **主入口模版**。负责根据 Frontmatter 配置组装各个模块（封面、目录、正文）。
- **`nb-lib.typ`**: **核心样式库**。定义了页眉页脚、标题样式、代码块高亮等基础排版规则。

### 封面变体 (Cover Styles)
通过 Frontmatter 的 `theme.coverstyle` 参数切换：
| 文件 | 说明 |
| :--- | :--- |
| `nb-cover-lib.typ` | 默认封面 (经典设计)。 |
| `nb-darkbg-cover-lib.typ` | 深色背景封面。 |
| `nb-big-cover-lib.typ` | 大图标/大图封面。 |
| `nb-report-cover-lib.typ` | 报告风格封面。 |

## 其他模版 (Root Templates)
位于 `src/mark2pdf/templates/` 根目录的简易模版

## 开发指引 (Pandoc Context)

模版可以使用 Pandoc 提供的上下文变量，例如：
- `$title$`, `$author$`, `$date`: 元数据。
- `$toc$`: 布尔值，是否显示目录。
- `$body$`: 正文内容 (Typst 源码)。

修改 `nb` 模版时，通常建议修改 `nb-lib.typ` 来调整通用样式，或修改对应的 `nb-*-cover-lib.typ` 来调整特定封面。
