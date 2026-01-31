"""集成测试用例。

测试各模块之间的协作和端到端流程。
"""

import re
import pytest
import pandas as pd
import sqlite3
from pathlib import Path
from docx import Document
from pypdf import PdfWriter

import unifiles
from unifiles import (
    read_excel,
    write_excel,
    read_docx,
    write_docx,
    query,
    get_schema,
    get_tables,
    extract_text,
    extract_tables,
)


def test_excel_to_sqlite_workflow(tmp_path: Path):
    """测试 Excel 数据导入到 SQLite 的完整流程。"""
    # 1. 创建 Excel 文件
    excel_file = tmp_path / "data.xlsx"
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
    write_excel(df, str(excel_file))

    # 2. 读取 Excel 文件
    df_read = read_excel(str(excel_file))

    # 3. 创建 SQLite 数据库并导入数据
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    df_read.to_sql("users", conn, if_exists="replace", index=False)
    conn.close()

    # 4. 查询 SQLite 数据库
    result = query(str(db_file), "SELECT * FROM users WHERE id > 1")
    assert len(result) == 2
    assert "Bob" in result["name"].values
    assert "Charlie" in result["name"].values


def test_excel_to_word_workflow(tmp_path: Path):
    """测试 Excel 数据导出到 Word 文档的流程。"""
    # 1. 创建 Excel 文件
    excel_file = tmp_path / "report.xlsx"
    df = pd.DataFrame({"项目": ["项目A", "项目B"], "状态": ["完成", "进行中"]})
    write_excel(df, str(excel_file))

    # 2. 读取 Excel 并转换为文本
    df_read = read_excel(str(excel_file))
    content = df_read.to_string(index=False)

    # 3. 写入 Word 文档
    word_file = tmp_path / "report.docx"
    write_docx(content, str(word_file), title="项目报告")

    # 4. 验证 Word 文档内容
    word_content = read_docx(str(word_file))
    assert "项目A" in word_content or "项目" in word_content


def test_sqlite_to_excel_workflow(tmp_path: Path):
    """测试 SQLite 数据导出到 Excel 的流程。"""
    # 1. 创建 SQLite 数据库并插入数据
    db_file = tmp_path / "data.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE products (id INTEGER, name TEXT, price REAL)")
    cursor.execute("INSERT INTO products VALUES (1, 'Product A', 10.5)")
    cursor.execute("INSERT INTO products VALUES (2, 'Product B', 20.0)")
    conn.commit()
    conn.close()

    # 2. 查询 SQLite 数据
    df = query(str(db_file), "SELECT * FROM products")

    # 3. 导出到 Excel
    excel_file = tmp_path / "products.xlsx"
    write_excel(df, str(excel_file))

    # 4. 验证 Excel 文件
    df_read = read_excel(str(excel_file))
    assert len(df_read) == 2
    assert "Product A" in df_read["name"].values


def test_all_modules_import():
    """测试所有模块都可以正常导入。"""
    # 测试主模块导入
    assert hasattr(unifiles, "read_excel")
    assert hasattr(unifiles, "write_excel")
    assert hasattr(unifiles, "read_docx")
    assert hasattr(unifiles, "write_docx")
    assert hasattr(unifiles, "query")
    assert hasattr(unifiles, "get_schema")
    assert hasattr(unifiles, "get_tables")
    assert hasattr(unifiles, "extract_text")
    assert hasattr(unifiles, "extract_tables")

    # 测试直接导入
    assert callable(read_excel)
    assert callable(write_excel)
    assert callable(read_docx)
    assert callable(write_docx)
    assert callable(query)
    assert callable(get_schema)
    assert callable(get_tables)
    assert callable(extract_text)
    assert callable(extract_tables)


def test_exception_hierarchy():
    """测试异常类的层次结构。"""
    from unifiles import (
        UnifilesError,
        FileFormatError,
        FileReadError,
        FileWriteError,
    )

    # 验证异常继承关系
    assert issubclass(FileFormatError, UnifilesError)
    assert issubclass(FileReadError, UnifilesError)
    assert issubclass(FileWriteError, UnifilesError)


def test_version():
    """测试版本号格式和存在性。"""
    # 验证版本号属性存在
    assert hasattr(unifiles, "__version__")

    # 验证版本号不为空
    version = unifiles.__version__
    assert version is not None
    assert isinstance(version, str)
    assert len(version) > 0

    # 验证版本号符合语义化版本格式（MAJOR.MINOR.PATCH）
    # 支持格式：1.2.3, 0.1.0, 1.0.0-alpha.1 等
    semver_pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$"
    assert re.match(
        semver_pattern, version
    ), f"版本号 '{version}' 不符合语义化版本格式 (MAJOR.MINOR.PATCH)"


def test_version_consistency():
    """测试版本号与 pyproject.toml 中的版本一致。"""
    # 优先使用标准库 tomllib（Python 3.11+），否则使用 tomli
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    # 读取 pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    # 获取 pyproject.toml 中的版本号
    pyproject_version = pyproject["project"]["version"]

    # 验证与代码中的版本号一致
    assert unifiles.__version__ == pyproject_version, (
        f"版本号不一致：代码中为 '{unifiles.__version__}'，"
        f"pyproject.toml 中为 '{pyproject_version}'"
    )
