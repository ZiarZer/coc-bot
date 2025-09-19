from typing import Optional
from enum import Enum
import os
import traceback


class LogLevel(Enum):
    DEBUG = '0'
    INFO = '1'
    NOTICE = '1;34'
    WARNING = '1;33'
    ERROR = '1;31'
    FATAL = '1;30'


def get_log_tag(log_level: Optional[LogLevel] = None) -> str:
    if log_level is None:
        return '         '
    return f'(\033[{log_level.value}m{log_level.name.rjust(7, " ").lower()}\033[0m)'


def log(message: str, log_level: Optional[LogLevel] = None) -> None:
    summary = traceback.extract_stack()[-2]
    print(f'{get_log_tag(log_level)} {message} \033[30m[{os.path.relpath(summary.filename)}:{summary.lineno}]\033[0m')
