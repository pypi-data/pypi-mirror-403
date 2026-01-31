"""Excel 文件操作模块。

提供 Excel 文件的读取、写入和查询功能。
"""

from typing import Any

import pandas as pd
from pathlib import Path

from .exceptions import FileReadError, FileWriteError


def read_excel(file_path: str, sheet_name: str | int | None = None) -> pd.DataFrame:
    """读取 Excel 文件内容。

    Args:
        file_path: Excel 文件路径
        sheet_name: 工作表名称或索引，None 表示读取第一个工作表

    Returns:
        包含 Excel 数据的 DataFrame 对象

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 工作表不存在或无效
        FileReadError: 读取文件时发生错误

    Example:
        >>> df = read_excel("data.xlsx", sheet_name="Sheet1")
        >>> print(df.head())
        >>> # 使用索引读取
        >>> df = read_excel("data.xlsx", sheet_name=0)
        >>> # 读取第一个工作表
        >>> df = read_excel("data.xlsx")
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    try:
        result = pd.read_excel(file_path, sheet_name=sheet_name)
        # 如果 sheet_name=None 且返回的是字典（只有一个工作表时也可能返回字典），提取第一个 DataFrame
        if sheet_name is None and isinstance(result, dict):
            if len(result) == 1:
                return list(result.values())[0]
            else:
                # 多个工作表时，返回第一个
                return list(result.values())[0]
        return result
    except FileNotFoundError:
        raise
    except ValueError as e:
        raise ValueError(f"工作表不存在或无效: {e}") from e
    except Exception as e:
        raise FileReadError(f"读取 Excel 文件失败: {e}") from e


def write_excel(
    data: pd.DataFrame | dict[str, pd.DataFrame],
    file_path: str,
    sheet_name: str = "Sheet1",
) -> None:
    """将数据写入 Excel 文件。

    支持写入单个 DataFrame 或多个 DataFrame（字典形式）。
    注意：此函数会覆盖整个目标文件，不保留原文件中的其他 Sheet。

    Args:
        data: 要写入的数据，可以是单个 DataFrame 或字典（多工作表）
        file_path: 输出 Excel 文件路径
        sheet_name: 工作表名称（当 data 为 DataFrame 时使用）

    Raises:
        ValueError: 数据格式无效
        PermissionError: 文件权限不足
        FileWriteError: 写入文件时发生错误

    Example:
        >>> # 写入单个 DataFrame
        >>> df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        >>> write_excel(df, "output.xlsx", sheet_name="Results")
        >>> # 写入多个工作表
        >>> data_dict = {"Sheet1": df1, "Sheet2": df2}
        >>> write_excel(data_dict, "output.xlsx")
    """
    if not isinstance(data, (pd.DataFrame, dict)):
        raise ValueError(
            f"数据格式无效，期望 DataFrame 或 dict，实际类型: {type(data)}"
        )

    # 如果是字典，先验证所有值都是 DataFrame
    if isinstance(data, dict):
        for sheet, df in data.items():
            if not isinstance(df, pd.DataFrame):
                raise ValueError(f"字典值必须是 DataFrame，实际类型: {type(df)}")

    try:
        if isinstance(data, pd.DataFrame):
            # 单个 DataFrame，写入指定工作表
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                data.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # 字典形式，写入多个工作表
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                for sheet, df in data.items():
                    df.to_excel(writer, sheet_name=sheet, index=False)
    except PermissionError:
        raise
    except Exception as e:
        raise FileWriteError(f"写入 Excel 文件失败: {e}") from e


def get_sheet_names(file_path: str) -> list[str]:
    """获取 Excel 文件中的所有工作表名称。

    Args:
        file_path: Excel 文件路径

    Returns:
        工作表名称列表

    Raises:
        FileNotFoundError: 文件不存在
        FileReadError: 读取文件时发生错误

    Example:
        >>> sheets = get_sheet_names("data.xlsx")
        >>> print(sheets)
        ['Sheet1', 'Sheet2']
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    try:
        # 使用 pandas.ExcelFile 获取工作表名称
        with pd.ExcelFile(file_path) as excel_file:
            sheet_names: list[str] = excel_file.sheet_names
            return sheet_names
    except FileNotFoundError:
        raise
    except Exception as e:
        raise FileReadError(f"获取工作表名称失败: {e}") from e


def get_column_names(
    file_path: str,
    sheet_name: str | int | None = None,
    header: int | None = 0,
    peek_rows: int = 0,
) -> list[str] | dict[int, list[str]]:
    """获取 Excel 工作表的列名。

    如果第一行不是列名，可以通过 header 参数指定列名所在行，或使用 peek_rows 预览前几行。

    Args:
        file_path: Excel 文件路径
        sheet_name: 工作表名称或索引，None 表示读取第一个工作表
        header: 列名所在行（0-based），0 表示第一行，1 表示第二行，None 表示无列名
        peek_rows: 如果大于 0，返回前 peek_rows 行的值（用于判断哪一行是列名）

    Returns:
        如果 peek_rows=0：返回列名列表
        如果 peek_rows>0：返回字典，键为行号（0-based），值为该行的值列表

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 工作表不存在或无效，或 header 超出范围
        FileReadError: 读取文件时发生错误

    Example:
        >>> # 默认获取第一行作为列名
        >>> columns = get_column_names("data.xlsx")
        >>> print(columns)
        ['姓名', '年龄', '城市']
        >>> # 指定第二行作为列名
        >>> columns = get_column_names("data.xlsx", header=1)
        >>> # 预览前 3 行，判断哪一行是列名
        >>> preview = get_column_names("data.xlsx", peek_rows=3)
        >>> print(preview)
        {0: ['姓名', '年龄', '城市'], 1: ['张三', 25, '北京'], 2: ['李四', 30, '上海']}
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    try:
        # 如果 peek_rows > 0，读取前几行用于预览
        if peek_rows > 0:
            # 读取前 peek_rows + 1 行（包含可能的 header 行）
            result_preview = pd.read_excel(
                file_path, sheet_name=sheet_name, nrows=peek_rows, header=None
            )
            # 处理 sheet_name=None 时返回字典的情况
            if isinstance(result_preview, dict):
                df_preview = list(result_preview.values())[0]
            else:
                df_preview = result_preview

            preview_dict: dict[int, list[str]] = {}
            for idx in range(min(peek_rows, len(df_preview))):
                # 将每行转换为列表，处理 NaN 值
                row_values = [
                    str(val) if pd.notna(val) else ""
                    for val in df_preview.iloc[idx].values
                ]
                preview_dict[idx] = row_values
            return preview_dict

        # 正常获取列名
        result = pd.read_excel(file_path, sheet_name=sheet_name, header=header)
        # 处理 sheet_name=None 时返回字典的情况
        if isinstance(result, dict):
            df = list(result.values())[0]
        else:
            df = result
        column_names: list[str] = list(df.columns)
        return column_names
    except FileNotFoundError:
        raise
    except ValueError as e:
        raise ValueError(f"工作表不存在或无效，或 header 超出范围: {e}") from e
    except Exception as e:
        raise FileReadError(f"获取列名失败: {e}") from e


def get_excel_info(
    file_path: str,
    include_preview: bool = False,
    preview_rows: int = 3,
) -> dict[str, Any]:
    """获取 Excel 文件的完整信息。

    返回整个 Excel 文件的信息，包括所有工作表的基本信息。这对于快速了解文件结构非常有用。

    Args:
        file_path: Excel 文件路径
        include_preview: 是否包含每个工作表的数据预览（默认 False，避免数据量大时性能问题）
        preview_rows: 如果 include_preview=True，每个工作表预览的行数（默认 3 行）

    Returns:
        包含文件信息的字典：
        - file_path: 文件路径
        - file_size: 文件大小（字节）
        - sheet_count: 工作表数量
        - sheet_names: 工作表名称列表
        - sheets: 每个工作表的详细信息列表，每个元素包含：
          - sheet_name: 工作表名称
          - row_count: 总行数（不包括列名行）
          - column_count: 总列数
          - column_names: 列名列表
          - preview: 数据预览（仅当 include_preview=True 时包含）

    Raises:
        FileNotFoundError: 文件不存在
        FileReadError: 读取文件时发生错误

    Example:
        >>> info = get_excel_info("data.xlsx")
        >>> print(info)
        {
            'file_path': 'data.xlsx',
            'file_size': 12345,
            'sheet_count': 3,
            'sheet_names': ['Sheet1', 'Sheet2', 'Sheet3'],
            'sheets': [
                {
                    'sheet_name': 'Sheet1',
                    'row_count': 100,
                    'column_count': 5,
                    'column_names': ['姓名', '年龄', '城市', '职位', '薪资']
                },
                ...
            ]
        }
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    try:
        # 获取文件大小
        file_size = path.stat().st_size

        # 获取所有工作表名称
        with pd.ExcelFile(file_path) as excel_file:
            sheet_names = excel_file.sheet_names

        # 获取每个工作表的信息
        sheets_info: list[dict[str, Any]] = []
        for sheet_name in sheet_names:
            # 读取工作表数据
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            sheet_info: dict[str, Any] = {
                "sheet_name": sheet_name,
                "row_count": len(df),
                "column_count": len(df.columns),
                "column_names": list(df.columns),
            }

            # 如果需要预览数据
            if include_preview:
                preview_df = df.head(preview_rows)
                preview_df_filled = preview_df.fillna(value=None)
                sheet_info["preview"] = preview_df_filled.to_dict("records")

            sheets_info.append(sheet_info)

        info: dict[str, Any] = {
            "file_path": str(path),
            "file_size": file_size,
            "sheet_count": len(sheet_names),
            "sheet_names": sheet_names,
            "sheets": sheets_info,
        }

        return info
    except FileNotFoundError:
        raise
    except Exception as e:
        raise FileReadError(f"获取 Excel 文件信息失败: {e}") from e


def get_sheet_info(
    file_path: str,
    sheet_name: str | int | None = None,
    preview_rows: int = 5,
) -> dict[str, Any]:
    """获取 Excel 工作表的基本信息。

    Args:
        file_path: Excel 文件路径
        sheet_name: 工作表名称或索引，None 表示读取第一个工作表
        preview_rows: 预览的行数（默认 5 行），用于展示数据样例

    Returns:
        包含工作表信息的字典：
        - sheet_name: 工作表名称
        - row_count: 总行数（不包括列名行）
        - column_count: 总列数
        - column_names: 列名列表
        - preview: 前 preview_rows 行的数据预览（DataFrame 的字典表示）

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 工作表不存在或无效
        FileReadError: 读取文件时发生错误

    Example:
        >>> info = get_sheet_info("data.xlsx", sheet_name="Sheet1")
        >>> print(info)
        {
            'sheet_name': 'Sheet1',
            'row_count': 100,
            'column_count': 5,
            'column_names': ['姓名', '年龄', '城市', '职位', '薪资'],
            'preview': [
                {'姓名': '张三', '年龄': 25, '城市': '北京', ...},
                {'姓名': '李四', '年龄': 30, '城市': '上海', ...},
                ...
            ]
        }
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    try:
        # 读取完整数据
        result = pd.read_excel(file_path, sheet_name=sheet_name)
        # 处理 sheet_name=None 时返回字典的情况
        if isinstance(result, dict):
            df = list(result.values())[0]
        else:
            df = result

        # 获取工作表名称
        if sheet_name is None:
            # 如果未指定，获取第一个工作表名称
            with pd.ExcelFile(file_path) as excel_file:
                actual_sheet_name = excel_file.sheet_names[0]
        elif isinstance(sheet_name, int):
            with pd.ExcelFile(file_path) as excel_file:
                actual_sheet_name = excel_file.sheet_names[sheet_name]
        else:
            actual_sheet_name = sheet_name

        # 获取基本信息
        row_count = len(df)
        column_count = len(df.columns)
        column_names = list(df.columns)

        # 获取预览数据（转换为字典列表，便于 JSON 序列化）
        preview_df = df.head(preview_rows)
        # 处理 NaN 值，转换为 None
        preview_df_filled = preview_df.fillna(value=None)
        preview = preview_df_filled.to_dict("records")

        info: dict[str, Any] = {
            "sheet_name": actual_sheet_name,
            "row_count": row_count,
            "column_count": column_count,
            "column_names": column_names,
            "preview": preview,
        }

        return info
    except FileNotFoundError:
        raise
    except ValueError as e:
        raise ValueError(f"工作表不存在或无效: {e}") from e
    except Exception as e:
        raise FileReadError(f"获取工作表信息失败: {e}") from e
