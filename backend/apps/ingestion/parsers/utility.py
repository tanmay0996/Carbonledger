import csv
import io
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

# UK grid average 2024: 0.207 kgCO2e per kWh (National Grid ESO)
GRID_EMISSION_FACTOR = Decimal('0.207')

REQUIRED_FIELDS = ['site_name', 'period_start', 'period_end', 'usage_kwh']


def parse(file_content: str) -> dict:
    success = []
    failed = []
    warnings = []

    reader = csv.DictReader(io.StringIO(file_content))

    for row_num, row in enumerate(reader, start=2):
        raw = dict(row)
        result, error, row_warnings = _parse_row(row_num, raw)
        if result is None:
            failed.append({'row': row_num, 'raw': raw, 'error': error})
        else:
            warnings.extend(row_warnings)
            success.append(result)

    return {'success': success, 'failed': failed, 'warnings': warnings}


def _parse_row(row_num: int, row: dict) -> tuple:
    row_warnings = []

    meter_id = row.get('meter_id', '').strip()
    if not meter_id:
        row_warnings.append({'row': row_num, 'msg': 'missing meter_id, row accepted with warning'})

    missing = [f for f in REQUIRED_FIELDS if not row.get(f, '').strip()]
    if missing:
        return None, f"missing required fields: {missing}", []

    usage_str = row['usage_kwh'].strip()
    try:
        usage_kwh = Decimal(usage_str)
    except InvalidOperation:
        return None, f"invalid usage_kwh '{usage_str}'", []

    if usage_kwh <= 0:
        return None, f"usage_kwh must be positive, got '{usage_kwh}'", []

    try:
        period_start = datetime.strptime(row['period_start'].strip(), '%Y-%m-%d').date()
        period_end = datetime.strptime(row['period_end'].strip(), '%Y-%m-%d').date()
    except ValueError as e:
        return None, f"invalid date: {e}", []

    if period_end <= period_start:
        return None, f"period_end must be after period_start", []

    period_days = (period_end - period_start).days
    spans_months = (period_start.year, period_start.month) != (period_end.year, period_end.month)
    if spans_months:
        row_warnings.append({'row': row_num, 'msg': f"billing period is {period_days} days, spans two calendar months"})

    co2e_kg = usage_kwh * GRID_EMISSION_FACTOR

    return {
        'row': row_num,
        'raw': row,
        'scope': 2,
        'source': 'utility',
        'activity_date': period_start,
        'description': f"electricity {row['site_name'].strip()} {period_start} to {period_end}",
        'location': row['site_name'].strip(),
        'meter_id': meter_id,
        'period_start': period_start,
        'period_end': period_end,
        'original_value': float(usage_kwh),
        'original_unit': 'kWh',
        'normalized_value': float(usage_kwh),
        'normalized_unit': 'kWh',
        'co2e_kg': float(co2e_kg),
    }, None, row_warnings
