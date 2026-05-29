import csv
import io
from datetime import datetime

DATE_FORMATS = [
    '%Y-%m-%d', '%Y%m%d', '%d/%m/%Y', '%m/%d/%Y',
    '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%Y', '%d.%m.%y',
    '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S',
]


def detect_delimiter(content: str) -> str:
    first = content.split('\n')[0]
    return ';' if first.count(';') > first.count(',') else ','


def resolve(row: dict, *aliases) -> str:
    """Return the value of the first matching alias (case-insensitive), or ''."""
    lower = {k.strip().lower(): v for k, v in row.items()}
    for alias in aliases:
        v = lower.get(alias.lower(), '').strip()
        if v:
            return v
    return ''


def parse_date(val: str):
    val = val.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognised date format '{val}'")


def make_reader(content: str, delimiter: str = None):
    if delimiter is None:
        delimiter = detect_delimiter(content)
    return csv.DictReader(io.StringIO(content), delimiter=delimiter)
