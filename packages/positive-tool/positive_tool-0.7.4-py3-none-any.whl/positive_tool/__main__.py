# TODO:完成__main__.py

import os
import sys

from rich.text import Text
from rich.style import Style

from positive_tool import pt

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


def main():
    funcs = {
        "pt.find_project_path": pt.find_project_path(
            "positive_tool",
            os.path.dirname(os.path.abspath(__file__)),
        ),
        "pt.bytes_to_mb": pt.bytes_to_mb(1000 * 1000),
    }
    for key in funcs:
        print(
            Text(str(key), style=Style(color="yellow"), end=""),
            end="",
        )
        print(Text(str(funcs[key]), end=""), end="")


if __name__ == "__main__":
    main()
