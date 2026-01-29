# YakultPDF Project Guide

## 项目定位

**YakultPDF** 是一个 Python 工具库 (Library/CLI)，基于 Pandoc 和 Typst 将 Markdown 转换为高质量 PDF。

本仓库是工具的 **源码仓库**，而非具体的内容仓库。

## 项目架构

```
.
├── src/                # 源码 (mark2pdf 包)
│   └── mark2pdf/       # 核心逻辑
├── _working/           # 【试验工作区】本项目内部用于测试和验证的工作区 (不打包)
├── docs/               # 用户文档 (使用指南、配置说明)
├── scripts/            # 辅助脚本 (构建、清理)
└── _logs/              # 开发日志 (Plan, Research)
```

## 核心流程

1.  **开发**: 修改 `src/` 下的代码。
2.  **验证**: 在 `_working/` 目录中运行命令测试效果。
    ```bash
    # 在 _working 目录测试
    cd _working
    uv run mark2pdf convert test.md
    ```
3.  **测试**: 运行 `pytest`。
    ```bash
    uv run pytest
    ```

## 关键文件/目录导航

| 路径 | 说明 | AGENTS.md |
| :--- | :--- | :--- |
| `src/mark2pdf` | 核心代码逻辑 | [查看](src/mark2pdf/AGENTS.md) |
| `src/mark2pdf/templates` | 模版系统 | [查看](src/mark2pdf/templates/AGENTS.md) |
| `docs/` | 用户使用文档 | [查看](docs/README.md) |

## 开发规则

- **运行环境**: 必须使用 `uv run`。
- **依赖管理**: 使用 `uv add/remove`。
- **文档维护**: 新增功能需同步更新 `docs/` 下的对应文档。