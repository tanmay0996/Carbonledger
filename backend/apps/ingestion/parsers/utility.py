import logging
from decimal import Decimal, InvalidOperation
from .utils import resolve, parse_date, make_reader

logger = logging.getLogger(__name__)

GRID_EMISSION_FACTOR = Decimal('0.207')

PERIOD_START = ['period_start', 'start_date', 'billing_start', 'from_date', 'date_from',
                'bill_from', 'period_from', 'start', 'from', 'billing_period_start']
PERIOD_END   = ['period_end', 'end_date', 'billing_end', 'to_date', 'date_to',
                'bill_to', 'period_to', 'end', 'to', 'billing_period_end']
USAGE_KWH    = ['usage_kwh', 'kwh', 'consumption', 'consumption_kwh', 'energy_kwh',
                'usage', 'electricity_kwh', 'energy', 'units', 'reading', 'amount_kwh']
SITE_NAME    = ['site_name', 'site', 'location', 'address', 'building',
                'facility', 'name', 'meter_name', 'place', 'property']
METER_ID     = ['meter_id', 'meter', 'meter_number', 'meter_ref', 'id', 'account']


def parse(file_content: str) -> dict:
    success, failed, warnings = [], [], []
    reader = make_reader(file_content)
    for row_num, row in enumerate(reader, start=2):
        raw = dict(row)
        result, error, row_warnings = _parse_row(row_num, raw)
        if result is None:
            failed.append({'row': row_num, 'raw': raw, 'error': error})
        else:
            warnings.extend(row_warnings)
            success.append(result)
    return {'success': success, 'failed': failed, 'warnings': warnings}


def _parse_row(row_num, row):
    row_warnings = []

    meter_id = resolve(row, *METER_ID)
    if not meter_id:
        row_warnings.append({'row': row_num, 'msg': 'missing meter_id, row accepted with warning'})

    site = resolve(row, *SITE_NAME) or 'Unknown site'

    start_str = resolve(row, *PERIOD_START)
    end_str   = resolve(row, *PERIOD_END)
    usage_str = resolve(row, *USAGE_KWH)

    if not start_str:
        return None, 'missing period start date column', []
    if not end_str:
        return None, 'missing period end date column', []
    if not usage_str:
        return None, 'missing electricity usage (kWh) column', []

    try:
        usage_kwh = Decimal(usage_str.replace(',', '.'))
    except InvalidOperation:
        return None, f"invalid usage value '{usage_str}'", []

    if usage_kwh <= 0:
        return None, f"usage must be positive, got '{usage_kwh}'", []

    try:
        period_start = parse_date(start_str)
        period_end   = parse_date(end_str)
    except ValueError as e:
        return None, str(e), []

    if period_end <= period_start:
        return None, 'period end must be after period start', []

    if (period_start.year, period_start.month) != (period_end.year, period_end.month):
        days = (period_end - period_start).days
        row_warnings.append({'row': row_num, 'msg': f"billing period ({days} days) spans two calendar months"})

    co2e_kg = usage_kwh * GRID_EMISSION_FACTOR

    return {
        'row': row_num, 'raw': row,
        'scope': 2, 'source': 'utility',
        'activity_date': period_start,
        'description': f"electricity {site} {period_start} to {period_end}",
        'location': site,
        'original_value': float(usage_kwh), 'original_unit': 'kWh',
        'normalized_value': float(usage_kwh), 'normalized_unit': 'kWh',
        'co2e_kg': float(co2e_kg),
        'warnings': row_warnings,
    }, None, row_warnings
