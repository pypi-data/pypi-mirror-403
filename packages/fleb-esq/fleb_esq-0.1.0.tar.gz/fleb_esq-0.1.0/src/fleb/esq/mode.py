import typing
import re
import sys
import atexit
from enum import Enum

import ctypes
from ctypes import wintypes

class Mode(Enum):
    DISABLED = 0
    AUTO = 1
    ENABLED = 2

DISABLED = Mode.DISABLED
AUTO = Mode.AUTO
ENABLED = Mode.ENABLED

_IS_TTY = sys.stdout.isatty()

_mode: Mode = Mode.AUTO if _IS_TTY else Mode.DISABLED
_revert_fn: typing.Callable[[], None] | None = None

def revert() -> None:
    global _revert_fn
    if _revert_fn is None: return
    _revert_fn()
    _revert_fn = None

def init() -> None:
    global _revert_fn, _mode
    if _mode is Mode.DISABLED: return
    if _revert_fn is not None: return
    if not _IS_TTY: return
    if not sys.platform.startswith("win"): return
    _revert_fn = _windows_enable_ansi()

def _windows_restore_mode(prev_terminal_mode: int) -> None:
    global _revert_fn
    ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), prev_terminal_mode)
    _revert_fn = None

def _windows_enable_ansi() -> typing.Callable[[], None] | None:
    kernel32 = ctypes.windll.kernel32
    stdout_handle = kernel32.GetStdHandle(-11)
    terminal_mode = ctypes.wintypes.DWORD()
    if not kernel32.GetConsoleMode(stdout_handle, ctypes.byref(terminal_mode)): return
    mode_value = terminal_mode.value
    kernel32.SetConsoleMode(stdout_handle, mode_value | 0x0004)
    return lambda: _windows_restore_mode(mode_value)

def no_init() -> None:
    global _revert_fn
    if _revert_fn is not None: return
    _revert_fn = lambda: None

def set(mode: Mode, term_init: bool = True) -> None:
    global _mode, _revert_fn
    if mode.value > Mode.DISABLED.value and term_init and not _revert_fn:
        init()
    elif mode is Mode.DISABLED and _mode.value > Mode.DISABLED.value:
        revert()
    _mode = mode

def get() -> Mode:
    if _mode is not Mode.AUTO: return _mode
    return Mode.ENABLED if _IS_TTY else Mode.DISABLED

atexit.register(revert)

__all__ = ["Mode", "set", "get", "init", "no_init", "revert"]
