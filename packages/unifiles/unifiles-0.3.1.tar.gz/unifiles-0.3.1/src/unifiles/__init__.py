"""unifiles - 统一的文件操作库。

提供跨文件类型的统一接口，简化 Python 中对不同类型文件的读取、写入、抽取和查询操作。
"""

__version__ = "0.3.1"

# 导出异常类
from .exceptions import (
    FileFormatError,
    FileReadError,
    FileWriteError,
    UnifilesError,
)

# Excel 模块
from .excel import (
    get_column_names,
    get_excel_info,
    get_sheet_info,
    get_sheet_names,
    read_excel,
    write_excel,
)

# Word 模块
from .word import read_docx, write_docx

# SQLite 模块
from .sqlite import get_database_info, get_schema, get_tables, query

# PDF 模块
from .pdf import extract_tables, extract_text

__all__ = [
    "__version__",
    "UnifilesError",
    "FileFormatError",
    "FileReadError",
    "FileWriteError",
    "read_excel",
    "write_excel",
    "get_sheet_names",
    "get_column_names",
    "get_sheet_info",
    "get_excel_info",
    "read_docx",
    "write_docx",
    "query",
    "get_schema",
    "get_tables",
    "get_database_info",
    "extract_text",
    "extract_tables",
]
