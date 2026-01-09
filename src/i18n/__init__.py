import os
from .fr import FR_LOCALE

LOCALES: dict[str, dict[str, str]] = {
    'FR': FR_LOCALE,
}

DEFAULT_LANGUAGE = 'FR'
env_language = os.environ.get('LANGUAGE', DEFAULT_LANGUAGE)
LANGUAGE = env_language
if env_language not in ('EN', 'FR'):
    LANGUAGE = DEFAULT_LANGUAGE


def add_ending_semicolon(translated_key):
    if LANGUAGE == 'FR':
        return f'{translated_key} :'
    return f'{translated_key}:'

def __(key: str, *args) -> str:
    real_key = key
    if key.endswith(':'):
        real_key = key[:-1]
    result = LOCALES[LANGUAGE].get(real_key, real_key)
    for i in range(len(args)):
        result = result.replace(f'%{i + 1}', str(args[i]))
    if key.endswith(':'):
        return add_ending_semicolon(result)
    return result
