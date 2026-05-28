import pytest
from apps.ingestion.parsers.utility import parse


VALID_CSV = """meter_id,site_name,tariff_type,period_start,period_end,usage_kwh,demand_kw,rate_per_kwh,total_cost_usd
MTR-001,Hamburg HQ,commercial_standard,2024-01-01,2024-01-31,48200.00,210.5,0.142,6844.40
MTR-002,Munich Plant,industrial_high_voltage,2024-02-01,2024-02-29,88600.00,365.0,0.118,10454.80
"""

MISSING_METER_CSV = """meter_id,site_name,tariff_type,period_start,period_end,usage_kwh,demand_kw,rate_per_kwh,total_cost_usd
,Hamburg HQ,commercial_standard,2024-01-01,2024-01-31,8900.00,42.0,0.142,1263.80
"""

MISSING_USAGE_CSV = """meter_id,site_name,tariff_type,period_start,period_end,usage_kwh,demand_kw,rate_per_kwh,total_cost_usd
MTR-012,Hannover Hub,commercial_standard,2024-01-01,2024-01-31,,112.3,0.139,
"""

CROSS_MONTH_CSV = """meter_id,site_name,tariff_type,period_start,period_end,usage_kwh,demand_kw,rate_per_kwh,total_cost_usd
MTR-003,Berlin Office,commercial_standard,2024-01-15,2024-02-14,22800.00,98.7,0.139,3169.20
"""

BAD_DATE_CSV = """meter_id,site_name,tariff_type,period_start,period_end,usage_kwh,demand_kw,rate_per_kwh,total_cost_usd
MTR-001,Hamburg HQ,commercial_standard,01-01-2024,31-01-2024,48200.00,210.5,0.142,6844.40
"""

REVERSED_DATE_CSV = """meter_id,site_name,tariff_type,period_start,period_end,usage_kwh,demand_kw,rate_per_kwh,total_cost_usd
MTR-001,Hamburg HQ,commercial_standard,2024-01-31,2024-01-01,48200.00,210.5,0.142,6844.40
"""


def test_valid_rows_succeed():
    result = parse(VALID_CSV)
    assert len(result['success']) == 2
    assert len(result['failed']) == 0


def test_scope_is_always_2():
    result = parse(VALID_CSV)
    for row in result['success']:
        assert row['scope'] == 2


def test_unit_stays_kwh():
    result = parse(VALID_CSV)
    for row in result['success']:
        assert row['normalized_unit'] == 'kWh'
        assert row['original_unit'] == 'kWh'


def test_co2e_calculation():
    result = parse(VALID_CSV)
    row = result['success'][0]
    assert abs(row['co2e_kg'] - 48200 * 0.207) < 0.01


def test_missing_meter_id_warns_but_succeeds():
    result = parse(MISSING_METER_CSV)
    assert len(result['success']) == 1
    assert len(result['failed']) == 0
    assert any('missing meter_id' in w['msg'] for w in result['warnings'])


def test_missing_usage_fails():
    result = parse(MISSING_USAGE_CSV)
    assert len(result['failed']) == 1
    assert 'missing required fields' in result['failed'][0]['error']


def test_cross_month_billing_warns():
    result = parse(CROSS_MONTH_CSV)
    assert len(result['success']) == 1
    assert any('spans two calendar months' in w['msg'] for w in result['warnings'])


def test_bad_date_format_fails():
    result = parse(BAD_DATE_CSV)
    assert len(result['failed']) == 1
    assert 'invalid date' in result['failed'][0]['error']


def test_reversed_dates_fail():
    result = parse(REVERSED_DATE_CSV)
    assert len(result['failed']) == 1
    assert 'period_end must be after' in result['failed'][0]['error']
