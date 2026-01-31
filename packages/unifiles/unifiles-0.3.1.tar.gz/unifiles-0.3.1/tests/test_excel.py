"""Excel 模块测试用例。"""

import pytest
import pandas as pd
from pathlib import Path

from unifiles.excel import (
    get_column_names,
    get_excel_info,
    get_sheet_info,
    get_sheet_names,
    read_excel,
    write_excel,
)
from unifiles.exceptions import FileReadError, FileWriteError


def test_read_excel_success(tmp_path: Path):
    """测试成功读取 Excel 文件。"""
    # 创建测试文件
    test_file = tmp_path / "test.xlsx"
    df_expected = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    # 使用 ExcelWriter 确保文件格式正确
    with pd.ExcelWriter(test_file, engine="openpyxl") as writer:
        df_expected.to_excel(writer, sheet_name="Sheet1", index=False)

    # 测试读取
    result = read_excel(str(test_file))
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert list(result.columns) == ["A", "B"]
    pd.testing.assert_frame_equal(result, df_expected)


def test_read_excel_sheet_name(tmp_path: Path):
    """测试指定工作表名称读取。"""
    test_file = tmp_path / "test.xlsx"
    df1 = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    df2 = pd.DataFrame({"C": [5, 6], "D": [7, 8]})

    with pd.ExcelWriter(test_file, engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="Sheet1", index=False)
        df2.to_excel(writer, sheet_name="Sheet2", index=False)

    # 读取指定工作表
    result = read_excel(str(test_file), sheet_name="Sheet2")
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["C", "D"]
    pd.testing.assert_frame_equal(result, df2)


def test_read_excel_sheet_index(tmp_path: Path):
    """测试使用索引读取工作表。"""
    test_file = tmp_path / "test.xlsx"
    df1 = pd.DataFrame({"A": [1, 2]})
    df2 = pd.DataFrame({"B": [3, 4]})

    with pd.ExcelWriter(test_file, engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="Sheet1", index=False)
        df2.to_excel(writer, sheet_name="Sheet2", index=False)

    # 使用索引读取第二个工作表
    result = read_excel(str(test_file), sheet_name=1)
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["B"]


def test_read_excel_file_not_found():
    """测试文件不存在的情况。"""
    with pytest.raises(FileNotFoundError, match="文件不存在"):
        read_excel("nonexistent.xlsx")


def test_read_excel_invalid_sheet(tmp_path: Path):
    """测试无效工作表的情况。"""
    test_file = tmp_path / "test.xlsx"
    df = pd.DataFrame({"A": [1, 2, 3]})
    df.to_excel(test_file, index=False)

    # 测试不存在的工作表名称
    with pytest.raises(ValueError, match="工作表不存在或无效"):
        read_excel(str(test_file), sheet_name="NonExistentSheet")

    # 测试超出范围的索引
    with pytest.raises(ValueError):
        read_excel(str(test_file), sheet_name=999)


def test_write_excel_dataframe(tmp_path: Path):
    """测试写入单个 DataFrame。"""
    test_file = tmp_path / "output.xlsx"
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

    write_excel(df, str(test_file), sheet_name="Results")

    # 验证文件已创建
    assert test_file.exists()

    # 验证内容
    result = read_excel(str(test_file), sheet_name="Results")
    pd.testing.assert_frame_equal(result, df)


def test_write_excel_dict(tmp_path: Path):
    """测试写入多工作表。"""
    test_file = tmp_path / "output.xlsx"
    df1 = pd.DataFrame({"A": [1, 2]})
    df2 = pd.DataFrame({"B": [3, 4]})
    data_dict = {"Sheet1": df1, "Sheet2": df2}

    write_excel(data_dict, str(test_file))

    # 验证文件已创建
    assert test_file.exists()

    # 验证两个工作表都存在
    sheets = get_sheet_names(str(test_file))
    assert "Sheet1" in sheets
    assert "Sheet2" in sheets

    # 验证内容
    result1 = read_excel(str(test_file), sheet_name="Sheet1")
    result2 = read_excel(str(test_file), sheet_name="Sheet2")
    pd.testing.assert_frame_equal(result1, df1)
    pd.testing.assert_frame_equal(result2, df2)


def test_write_excel_overwrite(tmp_path: Path):
    """测试覆盖文件，验证不保留原有其他 Sheet。"""
    test_file = tmp_path / "output.xlsx"

    # 第一次写入，包含两个工作表
    df1 = pd.DataFrame({"A": [1, 2]})
    df2 = pd.DataFrame({"B": [3, 4]})
    write_excel({"Sheet1": df1, "Sheet2": df2}, str(test_file))

    # 验证两个工作表都存在
    sheets_before = get_sheet_names(str(test_file))
    assert len(sheets_before) == 2
    assert "Sheet1" in sheets_before
    assert "Sheet2" in sheets_before

    # 第二次写入，只写入一个工作表
    df3 = pd.DataFrame({"C": [5, 6]})
    write_excel(df3, str(test_file), sheet_name="Sheet3")

    # 验证现在只有一个工作表
    sheets_after = get_sheet_names(str(test_file))
    assert len(sheets_after) == 1
    assert "Sheet3" in sheets_after
    assert "Sheet1" not in sheets_after
    assert "Sheet2" not in sheets_after


def test_write_excel_invalid_data(tmp_path: Path):
    """测试无效数据格式。"""
    test_file = tmp_path / "output.xlsx"

    # 测试非 DataFrame 和非 dict 类型
    with pytest.raises(ValueError, match="数据格式无效"):
        write_excel("invalid_data", str(test_file))

    # 测试 dict 中值不是 DataFrame
    with pytest.raises(ValueError, match="字典值必须是 DataFrame"):
        write_excel({"Sheet1": "invalid"}, str(test_file))


def test_get_sheet_names(tmp_path: Path):
    """测试获取工作表名称。"""
    test_file = tmp_path / "test.xlsx"
    df1 = pd.DataFrame({"A": [1]})
    df2 = pd.DataFrame({"B": [2]})
    df3 = pd.DataFrame({"C": [3]})

    with pd.ExcelWriter(test_file, engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="Sheet1", index=False)
        df2.to_excel(writer, sheet_name="Sheet2", index=False)
        df3.to_excel(writer, sheet_name="Sheet3", index=False)

    sheets = get_sheet_names(str(test_file))
    assert isinstance(sheets, list)
    assert len(sheets) == 3
    assert "Sheet1" in sheets
    assert "Sheet2" in sheets
    assert "Sheet3" in sheets


def test_get_sheet_names_file_not_found():
    """测试文件不存在的情况。"""
    with pytest.raises(FileNotFoundError, match="文件不存在"):
        get_sheet_names("nonexistent.xlsx")


def test_get_column_names_basic(tmp_path: Path):
    """测试基本获取列名功能。"""
    test_file = tmp_path / "test.xlsx"
    df = pd.DataFrame(
        {"姓名": ["张三", "李四"], "年龄": [25, 30], "城市": ["北京", "上海"]}
    )
    df.to_excel(test_file, index=False)

    columns = get_column_names(str(test_file))
    assert isinstance(columns, list)
    assert columns == ["姓名", "年龄", "城市"]


def test_get_column_names_with_header(tmp_path: Path):
    """测试指定 header 行获取列名。"""
    test_file = tmp_path / "test.xlsx"
    # 创建包含多行的 Excel，第二行是列名
    with pd.ExcelWriter(test_file, engine="openpyxl") as writer:
        # 第一行是标题
        pd.DataFrame([["标题行"] * 3]).to_excel(
            writer, sheet_name="Sheet1", index=False, header=False
        )
        # 第二行是列名
        pd.DataFrame([["姓名", "年龄", "城市"]]).to_excel(
            writer, sheet_name="Sheet1", index=False, header=False, startrow=1
        )
        # 数据行
        pd.DataFrame([["张三", 25, "北京"], ["李四", 30, "上海"]]).to_excel(
            writer, sheet_name="Sheet1", index=False, header=False, startrow=2
        )

    # 使用第二行作为列名（header=1）
    columns = get_column_names(str(test_file), header=1)
    assert isinstance(columns, list)
    assert columns == ["姓名", "年龄", "城市"]


def test_get_column_names_peek_rows(tmp_path: Path):
    """测试预览前几行功能。"""
    test_file = tmp_path / "test.xlsx"
    df = pd.DataFrame(
        {
            "姓名": ["张三", "李四", "王五"],
            "年龄": [25, 30, 28],
            "城市": ["北京", "上海", "广州"],
        }
    )
    df.to_excel(test_file, index=False)

    preview = get_column_names(str(test_file), peek_rows=3)
    assert isinstance(preview, dict)
    assert 0 in preview
    assert 1 in preview
    assert 2 in preview
    # 第一行应该是列名
    assert preview[0] == ["姓名", "年龄", "城市"]


def test_get_column_names_file_not_found():
    """测试文件不存在的情况。"""
    with pytest.raises(FileNotFoundError, match="文件不存在"):
        get_column_names("nonexistent.xlsx")


def test_get_column_names_invalid_sheet(tmp_path: Path):
    """测试无效工作表的情况。"""
    test_file = tmp_path / "test.xlsx"
    df = pd.DataFrame({"A": [1, 2, 3]})
    df.to_excel(test_file, index=False)

    with pytest.raises(ValueError, match="工作表不存在或无效"):
        get_column_names(str(test_file), sheet_name="NonExistentSheet")


def test_get_sheet_info_basic(tmp_path: Path):
    """测试获取工作表基本信息。"""
    test_file = tmp_path / "test.xlsx"
    df = pd.DataFrame(
        {
            "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
            "年龄": [25, 30, 28, 35, 22],
            "城市": ["北京", "上海", "广州", "深圳", "杭州"],
        }
    )
    df.to_excel(test_file, index=False, sheet_name="员工信息")

    info = get_sheet_info(str(test_file), sheet_name="员工信息")
    assert isinstance(info, dict)
    assert info["sheet_name"] == "员工信息"
    assert info["row_count"] == 5
    assert info["column_count"] == 3
    assert info["column_names"] == ["姓名", "年龄", "城市"]
    assert isinstance(info["preview"], list)
    assert len(info["preview"]) == 5  # 默认预览 5 行
    assert info["preview"][0] == {"姓名": "张三", "年龄": 25, "城市": "北京"}


def test_get_sheet_info_preview_rows(tmp_path: Path):
    """测试指定预览行数。"""
    test_file = tmp_path / "test.xlsx"
    df = pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "B": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        }
    )
    df.to_excel(test_file, index=False)

    info = get_sheet_info(str(test_file), preview_rows=3)
    assert len(info["preview"]) == 3
    assert info["row_count"] == 10


def test_get_sheet_info_empty_sheet(tmp_path: Path):
    """测试空工作表。"""
    test_file = tmp_path / "test.xlsx"
    df = pd.DataFrame({"A": [], "B": []})
    df.to_excel(test_file, index=False)

    info = get_sheet_info(str(test_file))
    assert info["row_count"] == 0
    assert info["column_count"] == 2
    assert info["column_names"] == ["A", "B"]
    assert len(info["preview"]) == 0


def test_get_sheet_info_file_not_found():
    """测试文件不存在的情况。"""
    with pytest.raises(FileNotFoundError, match="文件不存在"):
        get_sheet_info("nonexistent.xlsx")


def test_get_sheet_info_invalid_sheet(tmp_path: Path):
    """测试无效工作表的情况。"""
    test_file = tmp_path / "test.xlsx"
    df = pd.DataFrame({"A": [1, 2, 3]})
    df.to_excel(test_file, index=False)

    with pytest.raises(ValueError, match="工作表不存在或无效"):
        get_sheet_info(str(test_file), sheet_name="NonExistentSheet")


def test_get_excel_info_basic(tmp_path: Path):
    """测试获取 Excel 文件基本信息。"""
    test_file = tmp_path / "test.xlsx"
    df1 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    df2 = pd.DataFrame({"C": [7, 8], "D": [9, 10]})
    df3 = pd.DataFrame({"E": [11]})

    with pd.ExcelWriter(test_file, engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="Sheet1", index=False)
        df2.to_excel(writer, sheet_name="Sheet2", index=False)
        df3.to_excel(writer, sheet_name="Sheet3", index=False)

    info = get_excel_info(str(test_file))

    assert isinstance(info, dict)
    assert info["file_path"] == str(test_file)
    assert info["file_size"] > 0
    assert info["sheet_count"] == 3
    assert info["sheet_names"] == ["Sheet1", "Sheet2", "Sheet3"]
    assert len(info["sheets"]) == 3

    # 验证第一个工作表的信息
    sheet1_info = info["sheets"][0]
    assert sheet1_info["sheet_name"] == "Sheet1"
    assert sheet1_info["row_count"] == 3
    assert sheet1_info["column_count"] == 2
    assert sheet1_info["column_names"] == ["A", "B"]
    assert "preview" not in sheet1_info  # 默认不包含预览


def test_get_excel_info_with_preview(tmp_path: Path):
    """测试包含预览数据的 Excel 文件信息。"""
    test_file = tmp_path / "test.xlsx"
    df = pd.DataFrame(
        {
            "姓名": ["张三", "李四", "王五", "赵六"],
            "年龄": [25, 30, 28, 35],
            "城市": ["北京", "上海", "广州", "深圳"],
        }
    )
    df.to_excel(test_file, index=False)

    info = get_excel_info(str(test_file), include_preview=True, preview_rows=2)

    assert "preview" in info["sheets"][0]
    preview = info["sheets"][0]["preview"]
    assert isinstance(preview, list)
    assert len(preview) == 2
    assert preview[0] == {"姓名": "张三", "年龄": 25, "城市": "北京"}


def test_get_excel_info_single_sheet(tmp_path: Path):
    """测试单个工作表的 Excel 文件。"""
    test_file = tmp_path / "test.xlsx"
    df = pd.DataFrame({"A": [1, 2, 3]})
    df.to_excel(test_file, index=False)

    info = get_excel_info(str(test_file))

    assert info["sheet_count"] == 1
    assert len(info["sheets"]) == 1
    assert info["sheets"][0]["row_count"] == 3
    assert info["sheets"][0]["column_names"] == ["A"]


def test_get_excel_info_empty_sheet(tmp_path: Path):
    """测试包含空工作表的 Excel 文件。"""
    test_file = tmp_path / "test.xlsx"
    df = pd.DataFrame({"A": [], "B": []})
    df.to_excel(test_file, index=False)

    info = get_excel_info(str(test_file))

    assert info["sheet_count"] == 1
    assert info["sheets"][0]["row_count"] == 0
    assert info["sheets"][0]["column_count"] == 2
    assert info["sheets"][0]["column_names"] == ["A", "B"]


def test_get_excel_info_file_not_found():
    """测试文件不存在的情况。"""
    with pytest.raises(FileNotFoundError, match="文件不存在"):
        get_excel_info("nonexistent.xlsx")
