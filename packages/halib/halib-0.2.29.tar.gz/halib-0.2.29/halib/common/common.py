import os
import sys
import re
import arrow
import importlib

import rich
from rich import print
from rich.panel import Panel
from rich.console import Console
from rich.pretty import pprint, Pretty

from pathlib import Path, PureWindowsPath
from typing import Optional
from loguru import logger

import functools
from typing import Callable, List, Literal, Union
import time
import math

console = Console()


def seed_everything(seed=42):
    import random
    import numpy as np

    random.seed(seed)
    np.random.seed(seed)
    # import torch if it is available
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pprint("torch not imported, skipping torch seed_everything")
        pass


def now_str(sep_date_time="."):
    assert sep_date_time in [
        ".",
        "_",
        "-",
    ], "sep_date_time must be one of '.', '_', or '-'"
    now_string = arrow.now().format(f"YYYYMMDD{sep_date_time}HHmmss")
    return now_string


def pad_string(
    text: str,
    target_width: Union[int, float] = -1,
    pad_char: str = ".",
    pad_sides: List[Literal["left", "right"]] = ["left", "right"],  # type: ignore
) -> str:
    """
    Pads a string to a specific width or a relative multiplier width.

    Args:
        text: The input string.
        target_width:
            - If int (e.g., 20): The exact total length of the resulting string.
            - If float (e.g., 1.5): Multiplies original length (must be >= 1.0).
              (e.g., length 10 * 1.5 = target width 15).
        pad_char: The character to use for padding.
        pad_sides: A list containing "left", "right", or both.
    """
    current_len = len(text)

    # 1. Calculate the final integer target width
    if isinstance(target_width, float):
        if target_width < 1.0:
            raise ValueError(f"Float target_width must be >= 1.0, got {target_width}")
        # Use math.ceil to ensure we don't under-pad (e.g. 1.5 * 5 = 7.5 -> 8)
        final_width = math.ceil(current_len * target_width)
    else:
        final_width = target_width

    # 2. Return early if no padding needed
    if current_len >= final_width:
        return text

    # 3. Calculate total padding needed
    padding_needed = final_width - current_len

    # CASE 1: Pad Both Sides (Center)
    if "left" in pad_sides and "right" in pad_sides:
        left_pad_count = padding_needed // 2
        right_pad_count = padding_needed - left_pad_count
        return (pad_char * left_pad_count) + text + (pad_char * right_pad_count)

    # CASE 2: Pad Left Only (Right Align)
    elif "left" in pad_sides:
        return (pad_char * padding_needed) + text

    # CASE 3: Pad Right Only (Left Align)
    elif "right" in pad_sides:
        return text + (pad_char * padding_needed)

    return text


# ==========================================
# Usage Examples
# ==========================================
if __name__ == "__main__":
    s = "Hello"

    # 1. Default (Both sides / Center)
    print(f"'{pad_string(s, 11)}'")
    # Output: "'***Hello***'"

    # 2. Left Only
    print(f"'{pad_string(s, 10, '-', ['left'])}'")
    # Output: "'-----Hello'"

    # 3. Right Only
    print(f"'{pad_string(s, 10, '.', ['right'])}'")
    # Output: "'Hello.....'"


def norm_str(in_str):
    # Replace one or more whitespace characters with a single underscore
    norm_string = re.sub(r"\s+", "_", in_str)
    # Remove leading and trailing spaces
    norm_string = norm_string.strip()
    return norm_string


def pprint_box(obj, title="", border_style="green"):
    """
    Pretty print an object in a box.
    """
    rich.print(
        Panel(Pretty(obj, expand_all=True), title=title, border_style=border_style)
    )


def console_rule(msg, do_norm_msg=True, is_end_tag=False):
    msg = norm_str(msg) if do_norm_msg else msg
    if is_end_tag:
        console.rule(f"</{msg}>")
    else:
        console.rule(f"<{msg}>")


def console_log(func):
    def wrapper(*args, **kwargs):
        console_rule(func.__name__)
        result = func(*args, **kwargs)
        console_rule(func.__name__, is_end_tag=True)
        return result

    return wrapper


class ConsoleLog:
    def __init__(self, message):
        self.message = message

    def __enter__(self):
        console_rule(self.message)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        console_rule(self.message, is_end_tag=True)
        if exc_type is not None:
            print(f"An exception of type {exc_type} occurred.")
            print(f"Exception message: {exc_value}")


def linux_to_wins_path(path: str) -> str:
    """
    Convert a Linux-style WSL path (/mnt/c/... or /mnt/d/...) to a Windows-style path (C:\...).
    """
    # Handle only /mnt/<drive>/... style
    if (
        path.startswith("/mnt/")
        and len(path) > 6
        and path[5].isalpha()
        and path[6] == "/"
    ):
        drive = path[5].upper()  # Extract drive letter
        win_path = f"{drive}:{path[6:]}"  # Replace "/mnt/c/" with "C:/"
    else:
        win_path = path  # Return unchanged if not a WSL-style path
    # Normalize to Windows-style backslashes
    return str(PureWindowsPath(win_path))


DEFAULT_STACK_TRACE_MSG = "Caused by halib.common.common.pprint_stack_trace"


def pprint_stack_trace(
    msg: str = DEFAULT_STACK_TRACE_MSG,
    e: Optional[Exception] = None,
    force_stop: bool = False,
):
    """
    Print the current stack trace or the stack trace of an exception.
    """
    try:
        if e is not None:
            raise e
        else:
            raise Exception("pprint_stack_trace called")
    except Exception as e:
        # attach the exception trace to a warning
        global DEFAULT_STACK_TRACE_MSG
        if len(msg.strip()) == 0:
            msg = DEFAULT_STACK_TRACE_MSG
        logger.opt(exception=e).warning(msg)
        if force_stop:
            console.rule(
                "[red]Force Stop Triggered in <halib.common.pprint_stack_trace>[/red]"
            )
            sys.exit(1)


def pprint_local_path(
    local_path: str, get_wins_path: bool = False, tag: str = ""
) -> str:
    """
    Pretty-print a local path with emoji and clickable file:// URI.

    Args:
        local_path: Path to file or directory (Linux or Windows style).
        get_wins_path: If True on Linux, convert WSL-style path to Windows style before printing.
        tag: Optional console log tag.

    Returns:
        The file URI string.
    """
    p = Path(local_path).resolve()
    type_str = "📄" if p.is_file() else "📁" if p.is_dir() else "❓"

    if get_wins_path and os.name == "posix":
        # Try WSL → Windows conversion
        converted = linux_to_wins_path(str(p))
        if converted != str(p):  # Conversion happened
            file_uri = str(PureWindowsPath(converted).as_uri())
        else:
            file_uri = p.as_uri()
    else:
        file_uri = p.as_uri()

    content_str = f"{type_str} [link={file_uri}]{file_uri}[/link]"

    if tag:
        with ConsoleLog(tag):
            console.print(content_str)
    else:
        console.print(content_str)

    return file_uri


def log_func(
    func: Optional[Callable] = None, *, log_time: bool = False, log_args: bool = False
):
    """
    A decorator that logs the start/end of a function.
    Supports both @log_func and @log_func(log_time=True) usage.
    """
    # 1. HANDLE ARGUMENTS: If called as @log_func(log_time=True), func is None.
    # We return a 'partial' function that remembers the args and waits for the func.
    if func is None:
        return functools.partial(log_func, log_time=log_time, log_args=log_args)

    # 2. HANDLE DECORATION: If called as @log_func, func is the actual function.
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Safe way to get name (handles partials/lambdas)
        func_name = getattr(func, "__name__", "Unknown_Func")

        # Note: Ensure 'ConsoleLog' context manager is available in your scope
        with ConsoleLog(func_name):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            finally:
                # We use finally to ensure logging happens even if func crashes
                end = time.perf_counter()

                if log_time or log_args:

                    console.print(pad_string(f"Func <{func_name}> summary", 80))
                    if log_time:
                        console.print(f"{func_name} took {end - start:.6f} seconds")
                    if log_args:
                        console.print(f"Args: {args}, Kwargs: {kwargs}")

        return result

    return wrapper


def tcuda():
    NOT_INSTALLED = "Not Installed"
    GPU_AVAILABLE = "GPU(s) Available"
    ls_lib = ["torch", "tensorflow"]
    lib_stats = {lib: NOT_INSTALLED for lib in ls_lib}
    for lib in ls_lib:
        spec = importlib.util.find_spec(lib)  # ty:ignore[possibly-missing-attribute]
        if spec:
            if lib == "torch":
                import torch

                lib_stats[lib] = str(torch.cuda.device_count()) + " " + GPU_AVAILABLE
            elif lib == "tensorflow":
                import tensorflow as tf  # type: ignore

                lib_stats[lib] = (
                    str(len(tf.config.list_physical_devices("GPU")))
                    + " "
                    + GPU_AVAILABLE
                )
    console.rule("<CUDA Library Stats>")
    pprint(lib_stats)
    console.rule("</CUDA Library Stats>")
    return lib_stats
