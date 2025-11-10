from .logger import log, LogLevel
from datetime import datetime, timezone
from i18n import __


MONTH_NAMES = [
    __('January'),
    __('February'),
    __('March'),
    __('April'),
    __('May'),
    __('June'),
    __('July'),
    __('August'),
    __('September'),
    __('October'),
    __('November'),
    __('December')
]


def to_timestamp(str_date):
    # str_date = 20250708T133325.000Z
    return int(
        datetime(
            year=int(str_date[:4]),
            month=int(str_date[4:6]),
            day=int(str_date[6:8]),
            hour=int(str_date[9:11]),
            minute=int(str_date[11:13]),
            second=int(str_date[13:15]),
            tzinfo=timezone.utc
        ).timestamp()
    )


def format_number(n: int) -> str:
    s = str(n)
    begin = len(s) % 3
    formatted = [s[:begin]] if begin > 0 else []
    for i in range(begin, len(s), 3):
        formatted.append(s[i:i + 3])
    return ' '.join(formatted)


def parse_year_month(year_month_str: str) -> str:
    # month_year_str format: 2025-01 (month is 01-indexed)
    year, month = year_month_str.split('-')
    month = MONTH_NAMES[int(month) - 1]
    return f'{month} {year}'
