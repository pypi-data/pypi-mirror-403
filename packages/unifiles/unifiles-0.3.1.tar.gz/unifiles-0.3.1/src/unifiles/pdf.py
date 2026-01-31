"""PDF 文件操作模块。

提供 PDF 文件的文本提取和表格提取功能。
"""

import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from .exceptions import FileReadError


def extract_text(file_path: str, page_range: tuple[int, int] | None = None) -> str:
    """从 PDF 文件中提取文本内容。

    Args:
        file_path: PDF 文件路径
        page_range: 页码范围 (start, end)，1-based（从 1 开始），None 表示提取所有页面

    Returns:
        提取的文本内容，页面之间用换行符分隔

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 页码范围无效
        FileReadError: 读取文件时发生错误

    Example:
        >>> # 提取所有页面文本
        >>> text = extract_text("document.pdf")
        >>> # 提取第 1 到第 5 页
        >>> text = extract_text("document.pdf", page_range=(1, 5))
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    try:
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)

        if page_range is None:
            # 提取所有页面
            start_idx = 0
            end_idx = total_pages
        else:
            start, end = page_range
            # 验证范围
            if start < 1 or end < start or end > total_pages:
                raise ValueError(f"页码范围无效: {page_range}, 总页数: {total_pages}")
            # 转换为 0-based 索引
            start_idx = start - 1
            end_idx = end

        # 提取文本
        texts: list[str] = []
        for i in range(start_idx, end_idx):
            text = reader.pages[i].extract_text()
            texts.append(text)

        return "\n".join(texts)
    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        raise FileReadError(f"提取 PDF 文本失败: {e}") from e


def extract_tables(
    file_path: str, page_range: tuple[int, int] | None = None
) -> list[pd.DataFrame]:
    """从 PDF 文件中提取表格数据。

    **MVP 限制说明**:
    本函数基于 pypdf 的布局文本提取实现，仅支持基础表格提取。
    以下情况可能无法正确识别：
    - 合并单元格的表格
    - 多列布局的复杂表格
    - 嵌套表格
    - 图片中的表格
    - 没有明显分隔符的表格

    如需更好的表格提取效果，建议后续版本考虑引入 pdfplumber 等专业库。

    Args:
        file_path: PDF 文件路径
        page_range: 页码范围 (start, end)，1-based（从 1 开始），None 表示提取所有页面

    Returns:
        提取的表格列表，每个表格为一个 DataFrame

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 页码范围无效
        FileReadError: 读取文件时发生错误

    Example:
        >>> # 提取所有表格
        >>> tables = extract_tables("document.pdf")
        >>> # 提取第 1 到第 3 页的表格
        >>> tables = extract_tables("document.pdf", page_range=(1, 3))
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    try:
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)

        # 页面范围处理（与 extract_text 相同）
        if page_range is None:
            start_idx = 0
            end_idx = total_pages
        else:
            start, end = page_range
            if start < 1 or end < start or end > total_pages:
                raise ValueError(f"页码范围无效: {page_range}, 总页数: {total_pages}")
            start_idx = start - 1
            end_idx = end

        tables: list[pd.DataFrame] = []

        # 遍历页面，尝试提取表格
        for i in range(start_idx, end_idx):
            page = reader.pages[i]
            # 使用布局模式提取文本
            # 如果页面没有内容（如空白页），可能抛出异常，需要处理
            try:
                layout_text = page.extract_text(extraction_mode="layout")
            except (KeyError, AttributeError):
                # 如果布局模式失败（如空白页），尝试普通模式
                layout_text = page.extract_text()
                if not layout_text.strip():
                    # 空白页，跳过
                    continue

            # 简单的表格识别逻辑（MVP）
            # 尝试通过制表符或连续空格识别表格行
            lines = layout_text.split("\n")
            table_rows: list[list[str]] = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 如果行包含制表符或多个连续空格，可能是表格行
                if "\t" in line:
                    # 使用制表符分割
                    cols = [col.strip() for col in line.split("\t") if col.strip()]
                elif "  " in line:
                    # 使用多个连续空格分割（至少 2 个空格）
                    cols = [
                        col.strip() for col in re.split(r" {2,}", line) if col.strip()
                    ]
                else:
                    continue

                # 至少两列才认为是表格
                if len(cols) > 1:
                    table_rows.append(cols)

            # 如果找到表格行，创建 DataFrame
            if table_rows:
                # 尝试第一行作为表头（如果行数足够）
                if len(table_rows) > 1:
                    # 检查第一行是否看起来像表头（例如，都是字符串且较短）
                    header = table_rows[0]
                    data_rows = table_rows[1:]
                    try:
                        df = pd.DataFrame(data_rows, columns=header)
                    except Exception:
                        # 如果表头设置失败，使用默认列名
                        df = pd.DataFrame(table_rows)
                else:
                    df = pd.DataFrame(table_rows)
                tables.append(df)

        return tables
    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        raise FileReadError(f"提取 PDF 表格失败: {e}") from e
