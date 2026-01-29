from .positive_tool_exception import PositiveToolError


class ArgTypeError(PositiveToolError):
    """arg.ArgType的錯誤"""


class ArgTypeWrongTypeError(ArgTypeError):
    """參數錯誤"""


class ArgTypeInitError(ArgTypeError):
    """給ArgType的參數錯誤（初始化錯誤）"""


class ArgTypeUnknownType(ArgTypeWrongTypeError):
    """無法確認的類型"""


class FileTooLarge(ArgTypeError):
    """檔案過大"""


class ArgTypeNoTypehintError(ArgTypeError):
    """沒有type hint

    用於`ArgType.auto`"""
