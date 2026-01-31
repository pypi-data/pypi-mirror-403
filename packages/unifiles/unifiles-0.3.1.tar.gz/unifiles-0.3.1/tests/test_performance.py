"""性能测试用例。

验证各模块的性能指标是否符合要求。
"""

import time
import pytest
import pandas as pd
import sqlite3
from pathlib import Path
from docx import Document
from pypdf import PdfWriter

from unifiles import read_excel, write_excel, read_docx, query, extract_text


def test_excel_read_performance(tmp_path: Path):
    """测试 Excel 读取性能（1000行 < 1秒）。"""
    # 创建包含 1000 行的 Excel 文件
    excel_file = tmp_path / "large.xlsx"
    df = pd.DataFrame(
        {
            "A": range(1000),
            "B": [f"Item {i}" for i in range(1000)],
            "C": [i * 1.5 for i in range(1000)],
        }
    )
    write_excel(df, str(excel_file))

    # 测试读取性能
    start_time = time.time()
    result = read_excel(str(excel_file))
    elapsed_time = time.time() - start_time

    assert len(result) == 1000
    assert elapsed_time < 1.0, f"Excel 读取耗时 {elapsed_time:.2f} 秒，超过 1 秒限制"


def test_pdf_text_extraction_performance(tmp_path: Path):
    """测试 PDF 文本提取性能（10页 < 2秒）。"""
    # 创建包含 10 页的 PDF
    pdf_file = tmp_path / "large.pdf"
    writer = PdfWriter()

    for _ in range(10):
        writer.add_blank_page(width=612, height=792)

    with open(pdf_file, "wb") as f:
        writer.write(f)

    # 测试提取性能
    start_time = time.time()
    result = extract_text(str(pdf_file))
    elapsed_time = time.time() - start_time

    assert isinstance(result, str)
    assert elapsed_time < 2.0, f"PDF 文本提取耗时 {elapsed_time:.2f} 秒，超过 2 秒限制"


def test_word_read_performance(tmp_path: Path):
    """测试 Word 文档读取性能（普通文档 < 0.5秒）。"""
    # 创建 Word 文档
    word_file = tmp_path / "test.docx"
    doc = Document()
    for i in range(50):  # 添加 50 个段落
        doc.add_paragraph(f"这是第 {i+1} 段内容。")
    doc.save(word_file)

    # 测试读取性能
    start_time = time.time()
    result = read_docx(str(word_file))
    elapsed_time = time.time() - start_time

    assert isinstance(result, str)
    assert (
        elapsed_time < 0.5
    ), f"Word 文档读取耗时 {elapsed_time:.2f} 秒，超过 0.5 秒限制"


def test_sqlite_query_performance(tmp_path: Path):
    """测试 SQLite 查询性能（简单查询 < 0.1秒）。"""
    # 创建 SQLite 数据库并插入数据
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    # 插入 100 条记录
    for i in range(100):
        cursor.execute("INSERT INTO users VALUES (?, ?)", (i, f"User{i}"))
    conn.commit()
    conn.close()

    # 测试查询性能
    start_time = time.time()
    result = query(str(db_file), "SELECT * FROM users WHERE id > 50")
    elapsed_time = time.time() - start_time

    assert len(result) == 49  # id > 50 的记录数
    assert elapsed_time < 0.1, f"SQLite 查询耗时 {elapsed_time:.2f} 秒，超过 0.1 秒限制"


@pytest.mark.skip(reason="性能测试可能在不同环境下有差异，仅作为参考")
def test_all_performance_benchmarks(tmp_path: Path):
    """运行所有性能基准测试（可选，标记为 skip）。"""
    test_excel_read_performance(tmp_path)
    test_pdf_text_extraction_performance(tmp_path)
    test_word_read_performance(tmp_path)
    test_sqlite_query_performance(tmp_path)
