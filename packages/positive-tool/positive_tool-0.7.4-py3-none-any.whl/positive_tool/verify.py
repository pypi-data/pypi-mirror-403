import os
import inspect
import typing

from typing import Any, Iterable, Literal, Union, Callable
import functools

from .exceptions import exceptions


class ArgType:
    """`positive_tool`工具：檢查參數類別"""

    __slots__: list[str] = [
        "arg_name",
        "arg_value",
        "arg_type",
        "is_file",
        "is_folder",
        "is_exists",
        "check_dir_already_exists",
        "exists_file_size_limit_mb",
    ]

    def __init__(
        self,
        arg_name: str,
        arg_value: Any,
        arg_type: list[Any] | Iterable | Any,
        *,
        do_check_value_type: bool = True,
        is_exists: bool = False,
        is_file: bool = False,
        is_folder: bool = False,
        check_dir_already_exists: bool = False,
        exists_file_size_limit_mb: int | None = None,
    ) -> None:
        """
        __init__ 的 Docstring

        :param arg_name: arg名稱
        :type arg_name: str
        :param arg_value: 參數值
        :type arg_value: Any
        :param arg_type: 參數類別
        :type arg_type: list[Any] | Iterable | Any
        :param do_check_value_type: init後檢查參數
        :type do_check_value_type: bool
        :param is_exists: 是否存在
        :type is_exists: bool
        :param is_file: 是否為檔案
        :type is_file: bool
        :param is_folder: 是否是資料夾
        :type is_folder: bool
        :param check_dir_already_exists: 說明
        :type check_dir_already_exists: bool
        :param exists_file_size_limit_mb: 檔案大小限制，單位是MB，小於1代表無限制大小
        :type exists_file_size_limit_mb: int
        """
        # TODO:移除`is_exists`的檢查檔案為存在，只檢查存在
        # TODO: 整理程式碼
        # 檢查參數
        if is_file is True and is_folder is True:
            raise exceptions.arg.ArgTypeWrongTypeError(
                "`is_file` 和 `is_folder` 不能同時使用"
            )
        if (
            (is_exists is True) or (is_file is True) or (is_folder is True)
        ) and type(arg_value) not in [str, os.PathLike]:
            raise exceptions.arg.ArgTypeInitError("`is_exists` 參數類型錯誤！")
        if (exists_file_size_limit_mb is not None) and (
            (is_exists is False) or (is_file is False)
        ):
            raise exceptions.arg.ArgTypeInitError(
                "`exists_file_size_limit_mb`只能在檔案存在時使用！"
            )
        #
        self.arg_name: str = arg_name
        self.arg_value: Any = arg_value
        if type(arg_type) is list:
            self.arg_type = arg_type
        elif isinstance(type(arg_type), Iterable) is True:
            self.arg_type = list(arg_type)
        else:
            self.arg_type = [arg_type]
        self.is_exists: bool = is_exists
        self.is_file: bool = is_file
        self.is_folder: bool = is_folder
        self.check_dir_already_exists: bool = check_dir_already_exists
        self.exists_file_size_limit_mb: None | int = exists_file_size_limit_mb
        #
        if do_check_value_type is True:
            self.check_value_type()

    def check_value_type(self) -> None | typing.NoReturn:
        # TODO:待整理程式碼
        if self.arg_value is None:
            if None not in self.arg_type:
                self.raise_arg_wrong_type_error()
            else:
                return None
        else:
            for i in self.arg_type:
                if typing.get_origin(i) is None:
                    # 不是type hint
                    if type(i) is type(object):
                        # class
                        if type(self.arg_value) is i:
                            break
                    elif type(i) is not type(object):
                        if (
                            type(self.arg_value) is type(i)
                            and self.arg_value == i
                        ):
                            break
                elif typing.get_origin(i) in [Literal, Union]:
                    type_hint = typing.get_args(i)
                    break_loop = False
                    for i2 in type_hint:
                        if type(i2) is type(object):
                            # class
                            if type(self.arg_value) is i2:
                                break_loop = True
                                break
                        elif type(i2) is not type(object):
                            if (
                                type(self.arg_value) is type(i2)
                                and self.arg_value == i2
                            ):
                                break_loop = True

                    if break_loop is True:
                        break
            else:
                self.raise_arg_wrong_type_error()
        if (
            (self.is_exists is True)
            and (self.arg_value is not None)
            and (type(self.arg_value) is str)
        ):
            match os.path.exists(self.arg_value):
                case False:
                    # if os.path.exists(self.arg_value) is False:
                    if self.is_file is True:
                        raise FileNotFoundError(
                            f"找不到檔案： {self.arg_value}"
                        )
                    elif self.is_folder is True:
                        raise FileNotFoundError(
                            f"找不到資料夾： {self.arg_value}"
                        )
                case True:
                    # TODO:整理程式碼
                    if type(self.arg_value) is str:
                        match os.path.isfile(self.arg_value):  # type: ignore
                            case True:
                                if self.is_folder is True:
                                    raise exceptions.pt.DirWrongType(
                                        f"應為資料夾卻是檔案： {self.arg_value}"
                                    )
                                elif (
                                    self.is_file is True
                                    and self.exists_file_size_limit_mb
                                    is not None
                                    and (self.exists_file_size_limit_mb > 0)
                                ):
                                    if (
                                        os.path.getsize(
                                            self.arg_value  # type: ignore
                                        )
                                        > 0
                                    ) and (
                                        (
                                            os.path.getsize(
                                                self.arg_value  # type: ignore
                                            )
                                            / 1000
                                            / 1000
                                        )
                                        <= self.exists_file_size_limit_mb
                                    ):
                                        self.raise_arg_wrong_type_error()
                            case False:
                                if self.is_file is True:
                                    raise exceptions.pt.DirWrongType(
                                        f"應為檔案卻是資料夾： {self.arg_value}"
                                    )
                    else:
                        self.raise_arg_wrong_type_error()

    def raise_arg_wrong_type_error(self) -> typing.NoReturn:
        # TODO:更改錯誤類型
        # TODO:錯誤類型可自訂callback
        raise exceptions.arg.ArgTypeWrongTypeError(
            f"參數 {self.arg_name} 的類型錯誤，應為：{self.arg_type}，卻為：{type(self.arg_value)}！"
        )

    @classmethod
    def auto(cls, func: Callable | None = None):
        """從type hint建立ArgType

        此功能使用到inspect

        如需更好的性能請手動建立ArgType

        `ArgType.auto`"""
        if (isinstance(func, Callable) is False) or (func is None):
            raise exceptions.arg.ArgTypeWrongTypeError(
                "ArgType.auto應傳入Callable！"
            )
        else:
            sig = inspect.signature(func)
            type_hints = typing.get_type_hints(func)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 綁定實際傳入的引數到參數名稱
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                for param_name, value in bound_args.arguments.items():
                    try:
                        hint = type_hints[param_name]
                    except KeyError:
                        raise exceptions.arg.ArgTypeNoTypehintError(
                            f"{func.__name__}的{param_name}沒有type hint"
                        )
                    ArgType(param_name, value, [hint])
                return func(*args, **kwargs)

            return wrapper
