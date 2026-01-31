# unifiles

统一的文件操作库，为多种常见文件类型提供一致的读写、抽取与查询接口，简化 Python 中的日常文件处理。

## 特性

- **统一接口**：不同文件类型使用一致的 API 设计，降低学习成本
- **模块化**：按文件类型分模块，可单独导入使用
- **类型安全**：完整类型注解（Python 3.10+），支持静态检查
- **易于扩展**：便于增加新的文件类型支持

## 支持的文件类型

| 类型       | 扩展名          | 功能说明                     | 状态   |
|------------|-----------------|------------------------------|--------|
| Excel      | `.xlsx`, `.xls` | 读取、写入、获取工作表名称、获取列名、获取工作表/文件信息 | ✅ 已实现 |
| PDF        | `.pdf`          | 提取文本、提取表格（基础）   | ✅ 已实现 |
| Word       | `.docx`         | 读取、写入                    | ✅ 已实现 |
| SQLite     | `.db`, `.sqlite`| 执行查询、获取表结构、获取表名、获取数据库信息 | ✅ 已实现 |

> **说明**：PDF 表格抽取将基于 `pypdf`，仅适合基础表格；复杂版式、多列、合并单元格等可能不准，后续版本会评估引入 `pdfplumber` 等方案。

## 环境要求

- **Python**：3.10+（与 `pyproject.toml` 一致）
- **操作系统**：Windows 10+、主流 Linux、macOS 10.14+

## 安装

从源码安装（开发模式，含测试与类型检查等依赖）：

```powershell
git clone https://github.com/Asheng008/unifiles.git
cd unifiles
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

仅安装运行依赖：

```powershell
pip install -e .
```

使用依赖锁文件安装（推荐用于生产环境）：

```powershell
pip install -r requirements.txt
```

若已发布到 PyPI：

```bash
pip install unifiles
```

## 快速开始

### Excel（已实现）

```python
import unifiles

# 读取
df = unifiles.read_excel("data.xlsx", sheet_name="Sheet1")

# 获取所有工作表名称
sheets = unifiles.get_sheet_names("data.xlsx")

# 获取列名
columns = unifiles.get_column_names("data.xlsx", sheet_name="Sheet1")

# 获取工作表信息
sheet_info = unifiles.get_sheet_info("data.xlsx", sheet_name="Sheet1")

# 获取整个 Excel 文件信息
excel_info = unifiles.get_excel_info("data.xlsx", include_preview=True)

# 写入（覆盖整个文件）
unifiles.write_excel(df, "output.xlsx", sheet_name="Results")

# 多工作表写入
unifiles.write_excel({"Sheet1": df1, "Sheet2": df2}, "output.xlsx")
```

### PDF（已实现）

```python
import unifiles

# 提取全文
text = unifiles.extract_text("document.pdf")

# 提取指定页（1-based，从第 1 页开始）
text = unifiles.extract_text("document.pdf", page_range=(1, 5))

# 提取表格（基础表格，MVP 限制：复杂布局可能识别不准）
tables = unifiles.extract_tables("document.pdf", page_range=(1, 5))
for table in tables:
    print(table)
```

### Word（已实现）

```python
import unifiles

# 读取
content = unifiles.read_docx("document.docx")
print(content)

# 写入
unifiles.write_docx("Hello World", "output.docx", title="My Document")

# 写入多行内容
content = "第一行\n第二行\n第三行"
unifiles.write_docx(content, "output.docx", title="多行文档")
```

### SQLite（已实现）

```python
import unifiles

# 查询（支持参数化查询）
df = unifiles.query("database.db", "SELECT * FROM users WHERE age > ?", (18,))

# 使用字典参数化查询
df = unifiles.query("database.db", "SELECT * FROM users WHERE age > :age", {"age": 18})

# 获取表结构
schema = unifiles.get_schema("database.db", "users")
print(schema)  # {'id': 'INTEGER', 'name': 'TEXT', 'age': 'INTEGER'}

# 获取表名列表
tables = unifiles.get_tables("database.db")
print(tables)  # ['users', 'products', 'orders']

# 获取数据库完整信息
db_info = unifiles.get_database_info("database.db", include_preview=True)
print(db_info)  # 包含文件大小、表数量、每个表的详细信息等
```

## API 概览

| 模块   | 函数 | 说明                         | 状态   |
|--------|------|------------------------------|--------|
| Excel  | `read_excel(file_path, sheet_name=None)` | 读取为 DataFrame | ✅ 已实现 |
| Excel  | `write_excel(data, file_path, sheet_name="Sheet1")` | 写入（覆盖整个文件） | ✅ 已实现 |
| Excel  | `get_sheet_names(file_path)` | 返回工作表名称列表 | ✅ 已实现 |
| Excel  | `get_column_names(file_path, sheet_name=None, header=0, peek_rows=0)` | 返回列名列表或预览行 | ✅ 已实现 |
| Excel  | `get_sheet_info(file_path, sheet_name=None, preview_rows=5)` | 返回工作表详细信息 | ✅ 已实现 |
| Excel  | `get_excel_info(file_path, include_preview=False, preview_rows=3)` | 返回整个 Excel 文件信息 | ✅ 已实现 |
| PDF    | `extract_text(file_path, page_range=None)` | 提取文本 | ✅ 已实现 |
| PDF    | `extract_tables(file_path, page_range=None)` | 提取表格列表（MVP：基础表格） | ✅ 已实现 |
| Word   | `read_docx(file_path)` | 读取为字符串 | ✅ 已实现 |
| Word   | `write_docx(content, file_path, title=None)` | 写入文档 | ✅ 已实现 |
| SQLite | `query(db_path, sql, params=None)` | 执行 SQL，返回 DataFrame | ✅ 已实现 |
| SQLite | `get_schema(db_path, table_name)` | 返回字段名到类型的映射 | ✅ 已实现 |
| SQLite | `get_tables(db_path)` | 返回表名列表 | ✅ 已实现 |
| SQLite | `get_database_info(db_path, include_preview=False, preview_rows=3)` | 返回数据库完整信息 | ✅ 已实现 |

导入方式示例：

```python
import unifiles
df = unifiles.read_excel("data.xlsx")

# 或按需导入
from unifiles import (
    read_excel,
    write_excel,
    get_sheet_names,
    get_column_names,
    get_sheet_info,
    get_excel_info,
    read_docx,
    write_docx,
    extract_text,
    extract_tables,
    query,
    get_schema,
    get_tables,
    get_database_info,
)
from unifiles import (
    UnifilesError,
    FileFormatError,
    FileReadError,
    FileWriteError,
)
```

## 项目结构

```
unifiles/
├── .cursor/                   # Cursor 相关配置（可选）
├── .gitignore
├── LICENSE                    # MIT 许可证
├── CHANGELOG.md               # 面向用户的版本变更记录
├── HISTORY.md                 # 与助手的指令历史（内部记录）
├── pyproject.toml             # 项目配置与依赖
├── README.md                  # 项目说明（当前文档）
├── TECH_REQUIREMENTS.md       # 技术需求
├── DEVELOPMENT_PLAN.md        # 开发计划
├── AGENTS.md                  # 开发规范（面向 AI / 协作）
├── requirements.txt           # 依赖锁文件（可选）
├── publish_pypi.bat           # 本地一键发布到 PyPI 的批处理脚本
├── .github/workflows/         # GitHub Actions CI 配置
│   └── ci.yml
├── docs/                      # 技术文档（发布、CI/CD、版本管理）
│   ├── README.md
│   ├── 01-发布Python包到PyPI.md
│   ├── 02-使用GitHub-Actions搭建CI流水线.md
│   ├── 03-用GitHub-Actions自动发布到PyPI.md
│   └── 04-版本管理与发布节奏.md
├── src/
│   └── unifiles/
│       ├── __init__.py
│       ├── exceptions.py
│       ├── excel.py           # ✅ 已实现
│       ├── pdf.py             # ✅ 已实现
│       ├── word.py            # ✅ 已实现
│       └── sqlite.py          # ✅ 已实现
└── tests/
    ├── __init__.py
    ├── test_excel.py
    ├── test_pdf.py
    ├── test_word.py
    ├── test_sqlite.py
    ├── test_integration.py
    ├── test_performance.py
    └── fixtures/
        └── test_files/        # 测试用示例文件
```

## 开发与贡献

- **开发规范**：类型注解、错误处理、工作流等见 [AGENTS.md](AGENTS.md)
- **功能与接口设计**：见 [TECH_REQUIREMENTS.md](TECH_REQUIREMENTS.md)
- **阶段与任务安排**：见 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)
- **版本变更记录**：见 [CHANGELOG.md](CHANGELOG.md)，从下一个版本开始将严格按语义化版本管理
- **技术文档**：发布流程、CI/CD、版本管理等见 `docs/` 目录
- **提交前检查**：推送前建议先跑与 CI 一致的本地检查，见 [.cursor/commands/ci-commit-and-push.md](.cursor/commands/ci-commit-and-push.md)

本地开发建议步骤（Windows PowerShell）：

```powershell
# 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装为可编辑包及开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 类型检查
mypy src/unifiles/

# 格式检查与自动格式化
black --check src/ tests/
black src/ tests/
```

## 作者与维护者

- **作者**：Asheng (`w62745@qq.com`)
- **仓库**：<https://github.com/Asheng008/unifiles>
- 欢迎通过 Issues 或 Pull Request 参与贡献。

## 许可证

本项目采用 [MIT License](./LICENSE)。
