
# 方案：YakultPDF 支持 --no-cover 和 --no-toc

## 目标
让 CLI 支持不生成封面和目录。

## 核心设计 (Pseudo-code)

### 1. 命令行接口 (convert.py)
```python
# 增加布尔开关
command convert(..., no_cover, no_toc):
    # 将参数透传给内部上下文
    ctx = prepare_config(..., no_cover, no_toc)
    dispatch(ctx)
```

### 2. 配置对象 (options.py)
```python
class ConversionOptions:
    # 增加控制字段
    no_cover: bool = False
    no_toc: bool = False
```

### 3. 业务逻辑 (core.py)
```python
function execute_in_sandbox(..., options):
    disables = []
    
    # 将开关转换为 disables 列表元素
    if options.no_cover: disables.append("cover")
    if options.no_toc: disables.append("toc")
    
    # 传递给底层工具
    # 注意：disables 参数会与 frontmatter 中的配置合并或覆盖
    run_pandoc_typst(..., disables=disables)
```

### 4. 底层工具适配 (helper_typst.py)
```python
function _add_pandoc_arguments(cmd, kwargs):
    for k, v in kwargs:
        if is_list(v):
            # 关键点：将列表拆解为多个重复参数
            # pandoc -V disables=cover -V disables=toc
            for item in v:
                cmd.add("-V", f"{k}={item}")
        else:
            cmd.add("-V", f"{k}={v}")
```

## 待办事项
- [ ] helper_typst.py: 实现列表参数的展开
- [ ] options.py: 添加字段
- [ ] convert.py: 添加 CLI 参数并传递
- [ ] core.py: 实现 flag 到 disables 列表的转换逻辑

请审阅。
