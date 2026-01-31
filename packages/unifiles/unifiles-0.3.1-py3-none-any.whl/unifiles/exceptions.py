"""自定义异常类模块。

本模块定义了 unifiles 库使用的所有自定义异常类。
"""


class UnifilesError(Exception):
    """unifiles 基础异常类。

    所有 unifiles 自定义异常的基类。
    """

    pass


class FileFormatError(UnifilesError):
    """文件格式错误异常。

    当文件格式不符合预期或无法识别时抛出。

    Example:
        >>> raise FileFormatError("不支持的文件格式: .xyz")
    """

    pass


class FileReadError(UnifilesError):
    """文件读取错误异常。

    当读取文件时发生错误时抛出。

    Example:
        >>> raise FileReadError("读取文件失败: data.xlsx")
    """

    pass


class FileWriteError(UnifilesError):
    """文件写入错误异常。

    当写入文件时发生错误时抛出。

    Example:
        >>> raise FileWriteError("写入文件失败: output.xlsx")
    """

    pass
