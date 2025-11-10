import os
from enum import Enum
from typing import Optional, Any
from .fr import FR_LOCALE

LOCALES: dict[str, dict[str, str]] = {
    'FR': FR_LOCALE,
}

DEFAULT_LANGUAGE = 'FR'
env_language = os.environ.get('LANGUAGE', DEFAULT_LANGUAGE)
LANGUAGE = env_language
if env_language not in ('EN', 'FR'):
    LANGUAGE = DEFAULT_LANGUAGE


def __(key: str, *args) -> str:
    result = LOCALES[LANGUAGE].get(key, key)
    for i in range(len(args)):
        result = result.replace(f'%{i + 1}', str(args[i]))
    return result
