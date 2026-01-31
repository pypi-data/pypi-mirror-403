"""SQLite 数据库操作模块。

提供 SQLite 数据库的查询和元数据获取功能。
"""

from typing import Any

import sqlite3
from pathlib import Path

import pandas as pd
from pandas.errors import DatabaseError

from .exceptions import FileReadError


def query(db_path: str, sql: str, params: tuple | dict | None = None) -> pd.DataFrame:
    """执行 SQL 查询并返回 DataFrame。

    Args:
        db_path: SQLite 数据库文件路径
        sql: SQL 查询语句
        params: 查询参数，可以是 tuple（用于 ? 占位符）或 dict（用于 :name 占位符）

    Returns:
        包含查询结果的 DataFrame 对象

    Raises:
        FileNotFoundError: 数据库文件不存在
        sqlite3.Error: SQL 执行错误
        FileReadError: 读取数据库时发生错误

    Example:
        >>> # 简单查询
        >>> df = query("database.db", "SELECT * FROM users")
        >>> # 使用 tuple 参数化查询
        >>> df = query("database.db", "SELECT * FROM users WHERE age > ?", (18,))
        >>> # 使用 dict 参数化查询
        >>> df = query("database.db", "SELECT * FROM users WHERE age > :age", {"age": 18})
    """
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")

    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(sql, conn, params=params)
            return df
    except DatabaseError as e:
        # pandas 会将 sqlite3.Error 包装为 DatabaseError
        # 检查底层原因是否是 sqlite3.Error
        if isinstance(e.__cause__, sqlite3.Error):
            raise e.__cause__  # 抛出原始的 sqlite3.Error
        raise sqlite3.Error(str(e)) from e
    except sqlite3.Error:
        raise  # 保留原异常
    except Exception as e:
        raise FileReadError(f"执行 SQL 查询失败: {e}") from e


def get_schema(db_path: str, table_name: str) -> dict[str, str]:
    """获取表结构（字段名到字段类型的映射）。

    Args:
        db_path: SQLite 数据库文件路径
        table_name: 表名

    Returns:
        字段名到字段类型的字典映射

    Raises:
        FileNotFoundError: 数据库文件不存在
        ValueError: 表不存在
        FileReadError: 读取数据库时发生错误

    Example:
        >>> schema = get_schema("database.db", "users")
        >>> print(schema)
        {'id': 'INTEGER', 'name': 'TEXT', 'age': 'INTEGER'}
    """
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            rows = cursor.fetchall()

            if not rows:
                raise ValueError(f"表不存在: {table_name}")

            # PRAGMA table_info 返回: (cid, name, type, notnull, dflt_value, pk)
            # 提取 name (索引1) 和 type (索引2)
            schema: dict[str, str] = {row[1]: row[2] for row in rows}
            return schema
    except ValueError:
        raise
    except sqlite3.Error as e:
        raise FileReadError(f"获取表结构失败: {e}") from e
    except Exception as e:
        raise FileReadError(f"获取表结构失败: {e}") from e


def get_tables(db_path: str) -> list[str]:
    """获取数据库中所有表名列表。

    Args:
        db_path: SQLite 数据库文件路径

    Returns:
        表名列表（排除系统表）

    Raises:
        FileNotFoundError: 数据库文件不存在
        FileReadError: 读取数据库时发生错误

    Example:
        >>> tables = get_tables("database.db")
        >>> print(tables)
        ['users', 'products', 'orders']
    """
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            # 过滤系统表（以 sqlite_ 开头的表）
            user_tables: list[str] = [t for t in tables if not t.startswith("sqlite_")]
            return user_tables
    except sqlite3.Error as e:
        raise FileReadError(f"获取表名列表失败: {e}") from e
    except Exception as e:
        raise FileReadError(f"获取表名列表失败: {e}") from e


def get_database_info(
    db_path: str,
    include_preview: bool = False,
    preview_rows: int = 3,
) -> dict[str, Any]:
    """获取 SQLite 数据库的完整信息。

    返回整个数据库的信息，包括所有表的基本信息。这对于快速了解数据库结构非常有用。

    Args:
        db_path: SQLite 数据库文件路径
        include_preview: 是否包含每个表的数据预览（默认 False，避免数据量大时性能问题）
        preview_rows: 如果 include_preview=True，每个表预览的行数（默认 3 行）

    Returns:
        包含数据库信息的字典：
        - db_path: 数据库文件路径
        - file_size: 文件大小（字节）
        - table_count: 表数量
        - table_names: 表名列表
        - tables: 每个表的详细信息列表，每个元素包含：
          - table_name: 表名
          - row_count: 总行数
          - column_count: 总列数
          - column_names: 列名列表
          - column_types: 列类型字典（列名 -> 类型）
          - preview: 数据预览（仅当 include_preview=True 时包含）

    Raises:
        FileNotFoundError: 数据库文件不存在
        FileReadError: 读取数据库时发生错误

    Example:
        >>> info = get_database_info("database.db")
        >>> print(info)
        {
            'db_path': 'database.db',
            'file_size': 12345,
            'table_count': 3,
            'table_names': ['users', 'products', 'orders'],
            'tables': [
                {
                    'table_name': 'users',
                    'row_count': 100,
                    'column_count': 3,
                    'column_names': ['id', 'name', 'age'],
                    'column_types': {'id': 'INTEGER', 'name': 'TEXT', 'age': 'INTEGER'}
                },
                ...
            ]
        }
    """
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")

    try:
        # 获取文件大小
        file_size = path.stat().st_size

        # 获取所有表名
        table_names = get_tables(db_path)

        # 获取每个表的信息
        tables_info: list[dict[str, Any]] = []
        for table_name in table_names:
            # 获取表结构（列名和类型）
            schema = get_schema(db_path, table_name)
            column_names = list(schema.keys())
            column_types = schema

            # 获取行数
            row_count_df = query(db_path, f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = int(row_count_df.iloc[0]["count"])

            table_info: dict[str, Any] = {
                "table_name": table_name,
                "row_count": row_count,
                "column_count": len(column_names),
                "column_names": column_names,
                "column_types": column_types,
            }

            # 如果需要预览数据
            if include_preview:
                preview_df = query(
                    db_path, f"SELECT * FROM {table_name} LIMIT {preview_rows}"
                )
                # 处理 NaN 值，转换为 None，便于 JSON 序列化
                preview_df_filled = preview_df.fillna(value=None)
                table_info["preview"] = preview_df_filled.to_dict("records")

            tables_info.append(table_info)

        info: dict[str, Any] = {
            "db_path": str(path),
            "file_size": file_size,
            "table_count": len(table_names),
            "table_names": table_names,
            "tables": tables_info,
        }

        return info
    except FileNotFoundError:
        raise
    except Exception as e:
        raise FileReadError(f"获取数据库信息失败: {e}") from e
