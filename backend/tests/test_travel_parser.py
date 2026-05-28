import pytest
from apps.ingestion.parsers.travel import parse, _haversine


VALID_CSV = """trip_id,traveler_id,travel_type,origin,destination,depart_date,return_date,distance_km,cost_usd,currency,booking_class,vendor
TRP-001,EMP-001,flight,FRA,JFK,2024-01-08,2024-01-12,,1842.00,USD,economy,Lufthansa
TRP-002,EMP-002,hotel,Berlin,Berlin,2024-01-14,2024-01-17,,420.00,USD,,Marriott
TRP-003,EMP-003,car,Frankfurt,Hamburg,2024-01-15,2024-01-15,490.00,185.00,USD,,Sixt
TRP-004,EMP-004,rail,Berlin,Munich,2024-01-18,2024-01-18,585.00,210.00,USD,,Deutsche Bahn
"""

MISSING_ORIGIN_CSV = """trip_id,traveler_id,travel_type,origin,destination,depart_date,return_date,distance_km,cost_usd,currency,booking_class,vendor
TRP-005,EMP-001,flight,,,2024-03-15,2024-03-16,,380.00,USD,economy,Ryanair
"""

UNKNOWN_AIRPORT_CSV = """trip_id,traveler_id,travel_type,origin,destination,depart_date,return_date,distance_km,cost_usd,currency,booking_class,vendor
TRP-006,EMP-001,flight,XYZ,ABC,2024-03-12,2024-03-12,,410.00,USD,economy,FlyX
"""

KNOWN_AIRPORT_NO_DISTANCE_CSV = """trip_id,traveler_id,travel_type,origin,destination,depart_date,return_date,distance_km,cost_usd,currency,booking_class,vendor
TRP-007,EMP-001,flight,FRA,LHR,2024-03-12,2024-03-12,,410.00,USD,economy,Lufthansa
"""


def test_valid_rows_succeed():
    result = parse(VALID_CSV)
    assert len(result['success']) == 4
    assert len(result['failed']) == 0


def test_scope_is_always_3():
    result = parse(VALID_CSV)
    for row in result['success']:
        assert row['scope'] == 3


def test_flight_uses_haversine_when_no_distance():
    result = parse(VALID_CSV)
    flight = next(r for r in result['success'] if r['travel_type'] == 'flight')
    assert flight['co2e_kg'] > 0
    assert any('haversine' in w['msg'] for w in result['warnings'])


def test_hotel_calculated_per_night():
    result = parse(VALID_CSV)
    hotel = next(r for r in result['success'] if r['travel_type'] == 'hotel')
    # 3 nights (Jan 14 -> Jan 17)
    assert hotel['original_unit'] == 'nights'
    assert hotel['original_value'] == 3
    assert abs(hotel['co2e_kg'] - 3 * 31.0) < 0.01


def test_car_uses_given_distance():
    result = parse(VALID_CSV)
    car = next(r for r in result['success'] if r['travel_type'] == 'car')
    assert car['original_unit'] == 'km'
    assert abs(car['co2e_kg'] - 490 * 0.171) < 0.01


def test_rail_emission_factor():
    result = parse(VALID_CSV)
    rail = next(r for r in result['success'] if r['travel_type'] == 'rail')
    assert abs(rail['co2e_kg'] - 585 * 0.041) < 0.01


def test_flight_missing_origin_fails():
    result = parse(MISSING_ORIGIN_CSV)
    assert len(result['failed']) == 1
    assert 'origin' in result['failed'][0]['error']


def test_unknown_airport_fails():
    result = parse(UNKNOWN_AIRPORT_CSV)
    assert len(result['failed']) == 1
    assert 'unknown airport codes' in result['failed'][0]['error']


def test_haversine_fra_jfk():
    dist = _haversine('FRA', 'JFK')
    assert 6000 < dist < 7000


def test_haversine_unknown_returns_none():
    assert _haversine('XYZ', 'FRA') is None


def test_known_airports_no_distance_warns_and_succeeds():
    result = parse(KNOWN_AIRPORT_NO_DISTANCE_CSV)
    assert len(result['success']) == 1
    assert any('haversine' in w['msg'] for w in result['warnings'])
