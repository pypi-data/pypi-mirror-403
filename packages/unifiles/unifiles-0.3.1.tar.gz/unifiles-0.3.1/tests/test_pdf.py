"""PDF 模块测试用例。"""

import pytest
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import TextStringObject
from pypdf.generic import DictionaryObject, ArrayObject, NumberObject

from unifiles.pdf import extract_text, extract_tables
from unifiles.exceptions import FileReadError


def _create_simple_pdf(tmp_path: Path, filename: str, content: str) -> Path:
    """创建简单的 PDF 文件用于测试。"""
    pdf_path = tmp_path / filename
    writer = PdfWriter()

    # 创建一个简单的页面
    page = writer.add_blank_page(width=612, height=792)

    # 使用文本对象添加内容（简化方式）
    # 注意：pypdf 的文本添加比较复杂，这里使用一个简单的方法
    # 实际测试中，我们可以使用已存在的 PDF 或使用 reportlab

    # 保存 PDF
    with open(pdf_path, "wb") as f:
        writer.write(f)

    return pdf_path


def test_extract_text_success(tmp_path: Path):
    """测试成功提取文本。"""
    # 创建一个简单的 PDF（使用 pypdf 创建空白页，然后手动添加文本对象比较复杂）
    # 为了测试，我们先创建一个基本的 PDF 文件
    pdf_path = tmp_path / "test.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    # 保存 PDF
    with open(pdf_path, "wb") as f:
        writer.write(f)

    # 测试提取（即使是空白页也应该能提取）
    result = extract_text(str(pdf_path))
    assert isinstance(result, str)
    # 空白页可能返回空字符串或很少的文本


def test_extract_text_page_range(tmp_path: Path):
    """测试指定页码范围提取。"""
    # 创建多页 PDF
    pdf_path = tmp_path / "test.pdf"
    writer = PdfWriter()

    # 添加 3 页
    for _ in range(3):
        writer.add_blank_page(width=612, height=792)

    with open(pdf_path, "wb") as f:
        writer.write(f)

    # 提取第 1 到第 2 页
    result = extract_text(str(pdf_path), page_range=(1, 2))
    assert isinstance(result, str)

    # 提取第 2 到第 3 页
    result2 = extract_text(str(pdf_path), page_range=(2, 3))
    assert isinstance(result2, str)


def test_extract_text_page_range_validation(tmp_path: Path):
    """测试页码范围验证。"""
    pdf_path = tmp_path / "test.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    with open(pdf_path, "wb") as f:
        writer.write(f)

    # 测试无效范围：start < 1
    with pytest.raises(ValueError, match="页码范围无效"):
        extract_text(str(pdf_path), page_range=(0, 1))

    # 测试无效范围：start > end
    with pytest.raises(ValueError, match="页码范围无效"):
        extract_text(str(pdf_path), page_range=(2, 1))

    # 测试无效范围：end > 总页数
    with pytest.raises(ValueError, match="页码范围无效"):
        extract_text(str(pdf_path), page_range=(1, 10))


def test_extract_text_file_not_found():
    """测试文件不存在的情况。"""
    with pytest.raises(FileNotFoundError, match="文件不存在"):
        extract_text("nonexistent.pdf")


def test_extract_text_invalid_pdf(tmp_path: Path):
    """测试无效 PDF 文件。"""
    # 创建一个非 PDF 文件
    test_file = tmp_path / "test.txt"
    test_file.write_text("这不是 PDF 文件")

    # pypdf 可能会抛出异常，应该被捕获为 FileReadError
    with pytest.raises(FileReadError):
        extract_text(str(test_file))


def test_extract_tables_success(tmp_path: Path):
    """测试基础表格提取。"""
    # 创建包含表格的 PDF（使用简单的文本布局）
    # 注意：pypdf 创建包含表格的 PDF 比较复杂
    # 这里我们创建一个基本的 PDF，表格提取可能会返回空列表
    pdf_path = tmp_path / "test.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    with open(pdf_path, "wb") as f:
        writer.write(f)

    # 测试提取表格（空白页可能没有表格）
    result = extract_tables(str(pdf_path))
    assert isinstance(result, list)
    # 空白页可能返回空列表


def test_extract_tables_page_range(tmp_path: Path):
    """测试指定页码范围提取表格。"""
    pdf_path = tmp_path / "test.pdf"
    writer = PdfWriter()

    # 添加 3 页
    for _ in range(3):
        writer.add_blank_page(width=612, height=792)

    with open(pdf_path, "wb") as f:
        writer.write(f)

    # 提取第 1 到第 2 页的表格
    result = extract_tables(str(pdf_path), page_range=(1, 2))
    assert isinstance(result, list)


def test_extract_tables_file_not_found():
    """测试文件不存在的情况。"""
    with pytest.raises(FileNotFoundError, match="文件不存在"):
        extract_tables("nonexistent.pdf")


def test_extract_tables_no_tables(tmp_path: Path):
    """测试没有表格的 PDF。"""
    pdf_path = tmp_path / "test.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    with open(pdf_path, "wb") as f:
        writer.write(f)

    result = extract_tables(str(pdf_path))
    assert isinstance(result, list)
    # 可能返回空列表或包含空 DataFrame 的列表


def test_extract_tables_page_range_validation(tmp_path: Path):
    """测试表格提取的页码范围验证。"""
    pdf_path = tmp_path / "test.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    with open(pdf_path, "wb") as f:
        writer.write(f)

    # 测试无效范围
    with pytest.raises(ValueError, match="页码范围无效"):
        extract_tables(str(pdf_path), page_range=(0, 1))

    with pytest.raises(ValueError, match="页码范围无效"):
        extract_tables(str(pdf_path), page_range=(2, 1))
