import os
import logging
import tomllib

from typing import Self, Literal, Union, Any, NoReturn

from rich.logging import RichHandler

from .exceptions import exceptions
from .verify import ArgType


def find_project_path(
    project_name: str,
    start_find_path: os.PathLike | str = os.path.abspath(
        os.path.dirname(__file__)
    ),
    *,
    dir_deep_max: int = 15,
) -> os.PathLike | str:
    """
    find_project_path 可以在某些時候找到專案資料夾

    :param project_name: 專案名稱
    :type project_name: str
    :param start_find_path: 開始尋找的資料夾，預設為__file__（模組的資料夾，建議傳__file__）
    :type start_find_path: os.PathLike | str
    :param dir_deep_max: 資料夾的deep
    :type dir_deep_max: int
    """
    # 檢查參數
    ArgType("project_name", project_name, str)
    ArgType(
        "start_find_path",
        start_find_path,
        [os.PathLike, str],
        is_exists=True,
        is_folder=True,
    )
    ArgType("dir_deep_max", dir_deep_max, int)
    dir_deep_count: int = 0
    project_path: str | os.PathLike = start_find_path
    project_path_log: list[str] = []
    while True:
        if dir_deep_count >= dir_deep_max:
            raise exceptions.pt.DirDeepError(
                f"找不到專案資料夾，已收尋的資料夾深度： {dir_deep_count}，紀錄： {project_path_log}"
            )
        if os.path.basename(project_path) == project_name:
            break
        else:
            project_path = os.path.normpath(os.path.join(project_path, ".."))
            if len(project_path_log) > 0:
                if (
                    project_path
                    == project_path_log[(len(project_path_log) - 1)]
                ):
                    raise exceptions.pt.DirNotFoundError(
                        f"找不到： {project_name}，已搜尋深度： {dir_deep_count}，已搜尋資料夾： {project_path_log}"
                    )
            project_path_log.append(project_path)
        dir_deep_count += 1
    del project_path_log
    return project_path


def build_logger(
    log_file_path: str | os.PathLike,
    logger_name: str | None = None,
    log_level_file: Literal[0, 10, 20, 30, 40, 50] = 10,
    log_level_console: Literal[0, 10, 20, 30, 40, 50] = 20,
    *,
    with_rich_traceback: bool = True,
) -> logging.Logger:
    # 檢查參數類型
    ArgType(
        "log_file_path",
        log_file_path,
        [str, os.PathLike],
    )
    ArgType("logger_name", logger_name, [str, None])
    ArgType(
        "log_level_file",
        log_level_file,
        [0, 10, 20, 30, 40, 50],
    )
    ArgType(
        "log_level_console",
        log_level_console,
        [0, 10, 20, 30, 40, 50],
    )
    ArgType(
        "with_rich_traceback",
        with_rich_traceback,
        [bool],
    )
    # build_logger
    format = "%(asctime)s | %(name)s | %(levelname)s | [%(filename)s:%(lineno)d::%(funcName)s] | %(message)s"
    time_format = "[%Y-%m-%d %H:%M:%S]"
    # 建立 RichHandler
    console_handler = RichHandler(
        rich_tracebacks=with_rich_traceback,
        tracebacks_show_locals=True,
    )
    console_handler.setLevel(log_level_console)
    # 建立 FileHandler
    file_handler = logging.FileHandler(
        log_file_path, encoding="utf-8", mode="a"
    )
    file_handler.setLevel(log_level_file)
    # 設定 Formatter
    formatter = logging.Formatter(fmt=format, datefmt=time_format)
    file_handler.setFormatter(formatter)
    logging.basicConfig(
        level=logging.DEBUG,
        format=format,
        datefmt=time_format,
        handlers=[console_handler, file_handler],
    )
    #
    return logging.getLogger(logger_name)


type_hint_UInt_init_arg_arg_value = Union[int, float, "UInt"]


class UInt:
    """正數"""

    __slot__: list[str] = ["value"]

    def __init__(
        self,
        value: type_hint_UInt_init_arg_arg_value | Self,
    ) -> None:
        #
        arg_value = ArgType(
            "value",
            value,
            [type_hint_UInt_init_arg_arg_value, UInt],
        )
        #
        if type(value) is int:
            value_int = value
        elif type(value) in [float, UInt]:
            value_int = int(value)
        # elif isinstance(value, (float, str, SupportsInt)) is True:
        #     value_int = int(value)
        else:
            arg_value.raise_arg_wrong_type_error()
        #
        if value_int < 0:
            raise exceptions.pt.UIntValueError("UInt不能小於零！")
        else:
            self.value = value_int

    def _raise_uint_error(self) -> NoReturn:
        raise exceptions.pt.UIntValueError("UInt不能小於零！")

    def __add__(self, other: int | float | Self):
        """符號：`+`"""
        # arg檢查
        # ArgType("other", other, [int, float, UInt])
        #
        other_int: int
        if isinstance(other, (float)):
            other_int = int(other)
        elif isinstance(other, int):
            other_int = other
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError("僅支援int、float及UInt！")
        #
        if other_int < 0 and abs(other_int) > self.value:
            raise exceptions.pt.UIntValueError("UInt不能小於零！")
        else:
            result = UInt(self.value + other_int)
            return result

    def __iadd__(self, other: int | float | Self):
        """符號：`+=`"""
        other_int: int
        if isinstance(other, (float)):
            other_int = int(other)
        elif isinstance(other, int):
            other_int = other
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError
        #
        if other_int < 0 and abs(other_int) > self.value:
            raise exceptions.pt.UIntValueError("UInt不能小於零！")
        else:
            self.value += other_int
            return self

    def __radd__(self, other: int | float | Self):
        if isinstance(other, int):
            result = other + self.value
        elif isinstance(other, float):
            result = other + float(self.value)
        else:
            raise NotImplementedError
        return result

    def __sub__(self, other: int | float | Self):
        """符號：`-`"""
        other_int: int
        if isinstance(other, int):
            other_int = other
        elif isinstance(other, float):
            other_int = int(other)
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError
        #
        if other_int > 0 and abs(other_int) > self.value:
            raise exceptions.pt.UIntValueError("UInt不能小於零！")
        else:
            result = UInt(self.value - other_int)
            return result

    def __isub__(self, other: int | float | Self):
        """符號：`-=`"""
        if isinstance(other, (float)):
            other_int = int(other)
        elif isinstance(other, int):
            other_int = other
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError
        #
        if other_int > 0 and abs(other_int) > self.value:
            raise exceptions.pt.UIntValueError("UInt不能小於零！")
        else:
            self.value -= other_int
            return self

    def __rsub__(self, other: int | float | Self):
        if isinstance(other, int):
            result = other - self.value
        elif isinstance(other, float):
            result = other - float(self.value)
        else:
            raise NotImplementedError
        return result

    def __mul__(self, other: int | float | Self):
        """符號：`*`"""
        # ArgType("other", other, [int, float, UInt])
        #
        # TODO:isinstance改成type
        if isinstance(other, int):
            other_int = other
        elif isinstance(other, float):
            other_int = int(other)
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError
        #
        if other_int < 0 and other_int != 0:
            raise exceptions.pt.UIntValueError("UInt不能小於零！")
        else:
            result = UInt(self.value * other_int)
            return result

    def __imul__(self, other: int | float | Self):
        """符號：`*=`"""
        # ArgType("other", other, [int, float, UInt])
        #
        if isinstance(other, int):
            other_int = other
        elif isinstance(other, float):
            other_int = int(other)
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError
        #
        if other_int < 0:
            raise exceptions.pt.UIntValueError("UInt不能小於零！")
        else:
            self.value *= other_int
            return self

    def __rmul__(self, other: int | float | Self):
        if isinstance(other, int):
            result = other * self.value
        elif isinstance(other, float):
            result = other * float(self.value)
        else:
            raise NotImplementedError
        return result

    def __eq__(self, other: object) -> bool:
        """符號：`==`"""
        if isinstance(other, int):
            other_int = other
        elif isinstance(other, float):
            other_int = int(other)
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError
        return self.value == other_int

    def __ne__(self, other: object):
        """符號：`!=`"""
        if isinstance(other, int):
            other_int = other
        elif isinstance(other, float):
            other_int = int(other)
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError
        return self.value != other_int

    def __gt__(self, other: int | float | Self):
        """符號：`>`"""
        if isinstance(other, int):
            other_int = other
        elif isinstance(other, float):
            other_int = int(other)
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError
        return self.value > other_int

    def __ge__(self, other: int | float | Self):
        """符號：`>=`"""
        if isinstance(other, int):
            other_int = other
        elif isinstance(other, float):
            other_int = int(other)
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError
        return self.value >= other_int

    def __lt__(self, other: int | float | Self):
        """符號：`<`"""
        if isinstance(other, int):
            other_int = other
        elif isinstance(other, float):
            other_int = int(other)
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError
        return self.value < other_int

    def __le__(self, other):
        """符號：`<=`"""
        if isinstance(other, int):
            other_int = other
        elif isinstance(other, float):
            other_int = int(other)
        elif isinstance(other, UInt):
            other_int = other.value
        else:
            raise NotImplementedError
        return self.value <= other_int

    def __int__(self) -> int:
        return self.value

    def __float__(self) -> float:
        return float(self.value)

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"UInt({self.value})"


def bytes_to_mb(size: int) -> float:  # TODO:待改良
    return size / 1000 / 1000


def get_project_info(
    pyproject_file_path: str,
) -> "ProjectInfo":  # TODO: 寫測試
    #
    ArgType(
        "pyproject_file_path",
        pyproject_file_path,
        [str],
        is_exists=True,
        is_file=True,
    )
    #
    if bytes_to_mb(os.path.getsize(pyproject_file_path)) > 10:
        raise exceptions.arg.FileTooLarge(
            f"檔案過大，檔案：「{pyproject_file_path}」"
        )
    else:
        with open(pyproject_file_path, "r") as f:
            file_str = f.read()
        data = tomllib.loads(file_str)
        name = data["project"]["name"]
        version = data["project"]["version"]
        return ProjectInfo(name, project_version=version, auto_get=False)


class SemVer:  # TODO: 寫測試
    """語意化版本（SemVer）

    [詳見：https://semver.org/lang/zh-TW/](https://semver.org/lang/zh-TW/)

    `positive_tool`
    """

    major: Union[UInt, int]
    minor: Union[UInt, int]
    patch: Union[UInt, int]
    __slot__ = ["major", "minor", "patch"]

    def __init__(
        self,
        major: Union[UInt, int],
        minor: Union[UInt, int],
        patch: Union[UInt, int] = UInt(0),
    ) -> None:
        #
        ArgType("major", major, [UInt, int])
        ArgType("minor", minor, [UInt, int])
        ArgType("patch", patch, [UInt, int])
        #
        if type(major) is UInt:
            self.major = major
        else:
            self.major = UInt(major)
        if type(major) is UInt:
            self.minor = minor
        else:
            self.minor = UInt(minor)
        if type(major) is UInt:
            self.patch = patch
        else:
            self.patch = UInt(patch)

    @classmethod
    def parse(
        cls, item: Union[tuple[int, int, int], list[int], Self, str]
    ) -> Self | NoReturn:  # type: ignore
        #
        arg_item = ArgType("item", item, [tuple, list, SemVer, str])
        #
        if type(item) in [SemVer]:
            return cls(item.major, item.minor, item.patch)  # type: ignore
        elif type(item) in [tuple, list]:
            if len(item) > 3 or len(item) < 2:  # type: ignore
                arg_item.raise_arg_wrong_type_error()
            else:
                return cls(*item)  # type: ignore
        elif type(item) in [str]:
            ver: list[str] = item.split(".", 3)  # type: ignore
            if len(ver) > 3 or len(ver) < 2:
                arg_item.raise_arg_wrong_type_error()
            else:
                return cls(*[int(i) for i in ver])
        else:
            arg_item.raise_arg_wrong_type_error()

    def __gt__(self, other: Self) -> bool:
        """符號：`>`"""
        #
        ArgType("other", other, [SemVer])
        #
        if (
            self.major > other.major
            or (self.major >= other.major and self.minor > other.minor)
            or (
                self.major >= other.major
                and self.minor >= other.minor
                and self.patch > other.patch
            )
        ):
            return True
        else:
            return False

    def __lt__(self, other: Self) -> bool | NoReturn:
        """符號：`<`"""
        #
        ArgType("other", other, [SemVer])
        #
        if (
            (
                self.patch < other.patch
                and self.minor <= other.minor
                and self.major <= other.major
            )
            or (self.minor < other.minor and self.major <= other.major)
            or (self.major < other.major)
        ):
            return True
        else:
            return False

    def __eq__(self, other: Self | Any) -> bool | NoReturn:
        if type(other) is SemVer:
            return (
                self.major == other.major
                and self.minor == other.minor
                and self.patch == other.patch
            )
        else:
            raise NotImplementedError

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        return f"SemVer({self.major}, {self.minor}, {self.patch})"


class ProjectInfo:  # TODO: 寫測試
    """專案資訊

    `positive_tool`
    """

    __slot__: list[str] = [
        "project_name",
        "project_path",
        "project_version",
        "project_license_file_path",
    ]

    def __init__(
        self,
        project_name: str,
        *,
        project_path: str | os.PathLike | None = None,
        project_version: SemVer | tuple[int, int, int] | None = None,
        project_license_file_path: str | None = None,
        auto_get: bool = True,
    ) -> None:
        """
        __init__ 的 Docstring

        :param project_name: 專案名稱
        :type project_name: str
        :param project_path: 專案路徑（位子）
        :type project_path: str
        :param project_version: 專案版本
        :type project_version: SemVer | tuple[int, int, int]
        :param project_license: 專案協議
        :type project_license: str
        """
        self.project_name = project_name
        #
        need_auto_get = False
        if type(project_version) is SemVer:
            self.project_version = project_version
        elif project_version is None:
            need_auto_get = True
        else:
            self.project_version = SemVer.parse(project_version)
        if project_path is None:
            self.project_path = find_project_path(self.project_name)
        else:
            self.project_path = project_path
        self.project_license_file_path = project_license_file_path
        if auto_get is True and need_auto_get is True:
            data_from_file = get_project_info(os.path.join(self.project_path))
            if project_version is None:
                self.project_version = data_from_file.project_version

    def __repr__(self) -> str:
        text: str = f"""ProjectInfo(
    project_name={self.project_name},
    project_path={self.project_path},
    project_version={self.project_version},
    project_license_file_path={self.project_license_file_path},
)
"""
        return text

    def __str__(self) -> str:
        text = f"""
ProjectInfo(
└─{self.project_name}:
    ├─path={self.project_path}
    ├─version={self.project_version}
    └─license_file={self.project_license_file_path}
)
"""
        return text
