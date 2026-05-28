import csv
import io
import math
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

# kgCO2e per passenger-km (DEFRA 2023 values)
EMISSION_FACTORS = {
    'flight': Decimal('0.255'),   # economy long-haul average
    'hotel':  Decimal('0.0'),     # handled per night, not per km
    'car':    Decimal('0.171'),   # average rental car
    'rail':   Decimal('0.041'),
}

# kgCO2e per hotel night (average business hotel, DEFRA 2023)
HOTEL_FACTOR_PER_NIGHT = Decimal('31.0')

# Airport coordinates (lat, lon) for haversine fallback
AIRPORT_COORDS = {
    'FRA': (50.0333, 8.5706),
    'JFK': (40.6413, -73.7781),
    'MUC': (48.3538, 11.7861),
    'LHR': (51.4700, -0.4543),
    'DXB': (25.2532, 55.3657),
    'BOM': (19.0896, 72.8656),
    'SIN': (1.3644, 103.9915),
    'NRT': (35.7720, 140.3929),
    'ORD': (41.9742, -87.9073),
    'LAX': (33.9425, -118.4081),
    'CDG': (49.0097, 2.5479),
    'AMS': (52.3086, 4.7639),
    'TXL': (52.5597, 13.2877),
    'BER': (52.3667, 13.5033),
    'VIE': (48.1103, 16.5697),
    'HAM': (53.6304, 9.9882),
}

REQUIRED_FIELDS = ['trip_id', 'traveler_id', 'travel_type', 'depart_date']


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

    missing = [f for f in REQUIRED_FIELDS if not row.get(f, '').strip()]
    if missing:
        return None, f"missing required fields: {missing}", []

    travel_type = row['travel_type'].strip().lower()
    if travel_type not in EMISSION_FACTORS:
        return None, f"unknown travel_type '{travel_type}'", []

    try:
        depart_date = datetime.strptime(row['depart_date'].strip(), '%Y-%m-%d').date()
    except ValueError:
        return None, f"invalid depart_date '{row['depart_date']}'", []

    if travel_type == 'hotel':
        co2e_kg, original_value, original_unit, desc = _calc_hotel(row, row_num, row_warnings)
    else:
        co2e_kg, original_value, original_unit, desc = _calc_transport(
            row, travel_type, row_num, row_warnings
        )
        if co2e_kg is None:
            return None, desc, []

    return {
        'row': row_num,
        'raw': row,
        'scope': 3,
        'source': 'travel',
        'activity_date': depart_date,
        'description': desc,
        'location': f"{row.get('origin', '').strip()} -> {row.get('destination', '').strip()}",
        'traveler_id': row['traveler_id'].strip(),
        'travel_type': travel_type,
        'original_value': float(original_value),
        'original_unit': original_unit,
        'normalized_value': float(original_value),
        'normalized_unit': original_unit,
        'co2e_kg': float(co2e_kg),
    }, None, row_warnings


def _calc_hotel(row, row_num, row_warnings):
    nights = 1
    try:
        depart = datetime.strptime(row['depart_date'].strip(), '%Y-%m-%d').date()
        ret = datetime.strptime(row['return_date'].strip(), '%Y-%m-%d').date()
        nights = max(1, (ret - depart).days)
    except (ValueError, KeyError):
        row_warnings.append({'row': row_num, 'msg': 'could not compute hotel nights, defaulting to 1'})

    co2e_kg = HOTEL_FACTOR_PER_NIGHT * Decimal(str(nights))
    return co2e_kg, nights, 'nights', f"hotel stay {nights} night(s) in {row.get('destination', '').strip()}"


def _calc_transport(row, travel_type, row_num, row_warnings):
    distance_str = row.get('distance_km', '').strip()
    distance_km = None

    if distance_str:
        try:
            distance_km = Decimal(distance_str)
        except Exception:
            row_warnings.append({'row': row_num, 'msg': f"invalid distance_km '{distance_str}', will try haversine"})

    if distance_km is None and travel_type == 'flight':
        origin = row.get('origin', '').strip().upper()
        dest = row.get('destination', '').strip().upper()
        if not origin or not dest:
            return None, None, None, f"flight missing origin/destination and no distance_km"
        hav = _haversine(origin, dest)
        if hav is None:
            return None, None, None, f"unknown airport codes '{origin}'/'{dest}' and no distance_km"
        distance_km = Decimal(str(hav))
        row_warnings.append({'row': row_num, 'msg': f"distance computed via haversine for {origin}->{dest}: {hav:.0f} km"})

    if distance_km is None:
        return None, None, None, f"no distance available for {travel_type} trip"

    co2e_kg = distance_km * EMISSION_FACTORS[travel_type]
    origin = row.get('origin', '').strip()
    dest = row.get('destination', '').strip()
    return co2e_kg, distance_km, 'km', f"{travel_type} {origin} to {dest}"


def _haversine(iata_a: str, iata_b: str) -> float | None:
    if iata_a not in AIRPORT_COORDS or iata_b not in AIRPORT_COORDS:
        return None
    lat1, lon1 = AIRPORT_COORDS[iata_a]
    lat2, lon2 = AIRPORT_COORDS[iata_b]
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
