"""Safe filesystem operations with undo support."""

from .pathxio import (
    copy,
    move,
    remove,
    undo,
    pathxioError
)

__all__ = [
    "copy",
    "move",
    "remove",
    "undo",
    "pathxioError"
]

__version__ = "0.2.0"
__author__ = "holyholical"
