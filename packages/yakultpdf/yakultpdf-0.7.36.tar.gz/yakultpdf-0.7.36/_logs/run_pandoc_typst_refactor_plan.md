# run_pandoc_typst 函数重构计划

## 现状分析

**函数位置**: `src/mark2pdf/helper_typst/helper_typst.py` 第26-221行（196行）

**核心职责**: 运行 pandoc 将 markdown 转换为 PDF/typst，管理模板依赖

**现有测试**: `tests/test_run_pandoc_typst.py`（4个测试用例）
- test_single_file_template：单文件模板
- test_directory_template：目录式模板
- test_extra_arguments：额外参数
- test_output_typst：typst 输出格式

---

## 代码分析

当前函数可拆分为4个逻辑模块：

### 1. 模板复制（第86-148行，约60行）
- 判断模板类型（单文件/目录式）
- 目录式：平铺复制整个目录到工作目录
- 单文件：仅复制模板文件

### 2. 命令构建（第153-165行，约15行）
- 构建 pandoc 基础命令
- 添加字体路径
- 添加额外参数

### 3. 执行（第167-186行，约20行）
- subprocess.run 执行
- 检查返回码
- 验证输出文件

### 4. 清理（第188-221行，约30行）
- 删除复制的模板文件
- 异常处理
- 输出提示信息

---

## 第一阶段：加固单元测试

### 需要补充的测试用例

1. **模板复制测试**
   - 测试目录式模板的子目录复制（images/）
   - 测试隐藏文件跳过逻辑（.gitignore等）
   - 测试目标文件已存在的覆盖情况

2. **命令构建测试**
   - 测试字体路径添加
   - 测试 kwargs 参数转换（下划线→连字符）
   - 测试布尔值转换

3. **执行测试**
   - 测试 returncode != 0 的失败情况
   - 测试输出文件不存在的失败情况

4. **清理测试**
   - 测试失败时不清理
   - 测试目录清理

5. **边界情况**
   - 测试 to_typst=True 修改扩展名
   - 测试 verbose 输出

---

## 第二阶段：拆分函数

### 新函数设计

```
run_pandoc_typst()          # 主函数，保持原接口
├── _copy_template_to_workdir()    # 返回 (template_filename, cleanup_items)
├── _build_pandoc_command()        # 返回 cmd 列表
├── _execute_pandoc()              # 返回 bool
└── _cleanup_template_files()      # 无返回值
```

### 具体拆分

#### 1. `_copy_template_to_workdir(template_path, workdir_path, verbose) -> tuple[str, list[Path]]`

功能：复制模板到工作目录
返回：(模板文件名, 清理列表)

#### 2. `_build_pandoc_command(input_file, output_file, template_filename, font_paths, workdir, verbose, kwargs) -> list`

功能：构建完整的 pandoc 命令
返回：命令列表

#### 3. `_execute_pandoc(cmd, workdir, output_file, verbose) -> bool`

功能：执行 pandoc 并验证结果
返回：是否成功

#### 4. `_cleanup_template_files(cleanup_items, verbose) -> None`

功能：清理临时模板文件//无返回

---

## 第三阶段：实施步骤

### 步骤1：补充测试（重要！）
- [ ] 添加模板复制的边界测试
- [ ] 添加命令构建的参数测试
- [ ] 添加执行失败的测试
- [ ] 添加清理逻辑的测试
- [ ] 运行测试确保通过

### 步骤2：提取辅助函数
- [ ] 提取 `_copy_template_to_workdir()`
- [ ] 提取 `_build_pandoc_command()`
- [ ] 提取 `_execute_pandoc()` 
- [ ] 提取 `_cleanup_template_files()`
- [ ] 每步提取后运行测试

### 步骤3：简化主函数
- [ ] 主函数调用4个子函数
- [ ] 保持原有接口不变
- [ ] 目标：主函数 < 50 行

### 步骤4：验证
- [ ] 全部测试通过
- [ ] 手动测试端到端转换
- [ ] 更新迭代日志

---

## 预期结果

| 函数 | 行数 | 职责 |
|------|------|------|
| `run_pandoc_typst` | ~40行 | 主流程协调 |
| `_copy_template_to_workdir` | ~50行 | 模板复制 |
| `_build_pandoc_command` | ~20行 | 命令构建 |
| `_execute_pandoc` | ~30行 | 执行验证 |
| `_cleanup_template_files` | ~15行 | 清理 |

**总计**: ~155行（从196行减少约20%，但可读性大幅提升）

---

## 风险

1. 拆分后参数传递可能变复杂
2. 清理逻辑与执行逻辑紧密耦合（需在成功时清理）
3. 目录式模板的清理有边界情况

## 缓解措施

- 先写测试覆盖边界情况
- 小步提取，每步测试
- 保持 cleanup_items 列表作为状态传递
