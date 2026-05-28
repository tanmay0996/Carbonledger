import pytest
from apps.ingestion.parsers.sap import parse


VALID_CSV = """Buchungskreis;Werk;Materialnummer;Materialbezeichnung;Menge;Einheit;Buchungsdatum;Kostenstelle;Bewegungsart
1000;PLANT_1000;MAT-DSL-001;Diesel;500.000;L;20240103;CC_OPS_01;201
1000;PLANT_2000;MAT-HFO-003;Schweröl;1000.000;KG;20240110;CC_OPS_02;201
1000;PLANT_1000;MAT-DSL-001;Diesel;100.000;GAL;20240115;CC_OPS_01;201
"""

DIRTY_CSV = """Buchungskreis;Werk;Materialnummer;Materialbezeichnung;Menge;Einheit;Buchungsdatum;Kostenstelle;Bewegungsart
;PLANT_1000;MAT-DSL-001;Diesel;500.000;L;20240103;CC_OPS_01;201
1000;;MAT-DSL-001;Diesel;500.000;L;20240103;CC_OPS_01;201
1000;PLANT_1000;MAT-DSL-001;Diesel;NOTANUMBER;L;20240103;CC_OPS_01;201
1000;PLANT_1000;MAT-DSL-001;Diesel;500.000;L;99991301;CC_OPS_01;201
1000;PLANT_1000;MAT-DSL-001;Diesel;500.000;BARREL;20240103;CC_OPS_01;201
1000;PLANT_1000;MAT-UNKNOWN;Unknown;500.000;L;20240103;CC_OPS_01;201
"""

UNKNOWN_PLANT_CSV = """Buchungskreis;Werk;Materialnummer;Materialbezeichnung;Menge;Einheit;Buchungsdatum;Kostenstelle;Bewegungsart
1000;PLANT_9999;MAT-DSL-001;Diesel;500.000;L;20240103;CC_OPS_01;201
"""


def test_valid_rows_all_succeed():
    result = parse(VALID_CSV)
    assert len(result['success']) == 3
    assert len(result['failed']) == 0


def test_scope_is_always_1():
    result = parse(VALID_CSV)
    for row in result['success']:
        assert row['scope'] == 1


def test_liters_conversion_gallon():
    result = parse(VALID_CSV)
    gal_row = next(r for r in result['success'] if r['original_unit'] == 'GAL')
    assert abs(gal_row['normalized_value'] - 100 * 3.78541) < 0.01
    assert gal_row['normalized_unit'] == 'L'


def test_kg_to_liters_hfo():
    result = parse(VALID_CSV)
    hfo_row = next(r for r in result['success'] if 'heavy_fuel_oil' in r['description'])
    assert hfo_row['normalized_unit'] == 'L'
    assert hfo_row['normalized_value'] > 0


def test_co2e_is_positive():
    result = parse(VALID_CSV)
    for row in result['success']:
        assert row['co2e_kg'] > 0


def test_dirty_rows_all_fail():
    result = parse(DIRTY_CSV)
    assert len(result['success']) == 0
    assert len(result['failed']) == 6


def test_missing_buchungskreis_fails():
    result = parse(DIRTY_CSV)
    errors = [r['error'] for r in result['failed']]
    assert any('missing required fields' in e for e in errors)


def test_invalid_quantity_fails():
    result = parse(DIRTY_CSV)
    errors = [r['error'] for r in result['failed']]
    assert any('invalid quantity' in e for e in errors)


def test_invalid_date_fails():
    result = parse(DIRTY_CSV)
    errors = [r['error'] for r in result['failed']]
    assert any('invalid date' in e for e in errors)


def test_unknown_unit_fails():
    result = parse(DIRTY_CSV)
    errors = [r['error'] for r in result['failed']]
    assert any('unsupported unit' in e for e in errors)


def test_unknown_plant_produces_warning():
    result = parse(UNKNOWN_PLANT_CSV)
    assert len(result['success']) == 1
    assert len(result['warnings']) == 1
    assert 'unknown plant code' in result['warnings'][0]['msg']


def test_activity_date_parsed():
    result = parse(VALID_CSV)
    from datetime import date
    assert result['success'][0]['activity_date'] == date(2024, 1, 3)
