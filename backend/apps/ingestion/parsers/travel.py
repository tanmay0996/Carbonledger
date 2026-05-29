import math
import logging
from datetime import datetime
from decimal import Decimal
from .utils import resolve, parse_date, make_reader

logger = logging.getLogger(__name__)

EMISSION_FACTORS = {
    'flight': Decimal('0.255'),
    'hotel':  Decimal('0.0'),
    'car':    Decimal('0.171'),
    'rail':   Decimal('0.041'),
}

HOTEL_FACTOR_PER_NIGHT = Decimal('31.0')

AIRPORT_COORDS = {
    'FRA': (50.0333,  8.5706), 'JFK': (40.6413, -73.7781),
    'MUC': (48.3538, 11.7861), 'LHR': (51.4700,  -0.4543),
    'DXB': (25.2532, 55.3657), 'BOM': (19.0896,  72.8656),
    'SIN': ( 1.3644,103.9915), 'NRT': (35.7720, 140.3929),
    'ORD': (41.9742, -87.9073),'LAX': (33.9425,-118.4081),
    'CDG': (49.0097,  2.5479), 'AMS': (52.3086,   4.7639),
    'TXL': (52.5597, 13.2877), 'BER': (52.3667,  13.5033),
    'VIE': (48.1103, 16.5697), 'HAM': (53.6304,   9.9882),
    'HEL': (60.3172, 24.9633), 'CPH': (55.6180,  12.6561),
    'BCN': (41.2974,  2.0833), 'MAD': (40.4983,  -3.5676),
    'FCO': (41.8003, 12.2389), 'ZRH': (47.4647,   8.5492),
    'BRU': (50.9014,  4.4844), 'VIE': (48.1103,  16.5697),
}

TRAVEL_TYPE_MAP = {
    'flight': 'flight', 'air': 'flight', 'airplane': 'flight',
    'plane': 'flight', 'fly': 'flight', 'flying': 'flight', 'aviation': 'flight',
    'car': 'car', 'automobile': 'car', 'vehicle': 'car', 'drive': 'car',
    'road': 'car', 'rental': 'car', 'car_rental': 'car', 'taxi': 'car', 'uber': 'car',
    'rail': 'rail', 'train': 'rail', 'railway': 'rail', 'metro': 'rail', 'tram': 'rail',
    'hotel': 'hotel', 'accommodation': 'hotel', 'lodging': 'hotel',
    'stay': 'hotel', 'overnight': 'hotel', 'motel': 'hotel',
}

TYPE_COL     = ['travel_type', 'type', 'mode', 'expense_type', 'trip_type', 'transport_type', 'category', 'travel_mode']
DATE_COL     = ['depart_date', 'date', 'departure_date', 'trip_date', 'start_date', 'from_date', 'travel_date', 'booking_date']
RETURN_COL   = ['return_date', 'end_date', 'to_date', 'arrival_date', 'return', 'check_out']
ORIGIN_COL   = ['origin', 'from', 'departure', 'from_city', 'from_airport', 'departure_city', 'start', 'origin_city']
DEST_COL     = ['destination', 'to', 'arrival', 'to_city', 'to_airport', 'arrival_city', 'end', 'destination_city']
DISTANCE_COL = ['distance_km', 'distance', 'km', 'kilometers', 'dist', 'kilometres']
MILES_COL    = ['distance_miles', 'miles', 'mi']
TRAVELER_COL = ['traveler_id', 'traveler', 'employee', 'employee_id', 'user_id', 'person_id', 'name', 'passenger']
TRIP_COL     = ['trip_id', 'id', 'booking_id', 'reference', 'ref', 'trip_ref', 'booking_ref']


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

    type_raw = resolve(row, *TYPE_COL)
    if not type_raw:
        return None, 'missing travel type column (flight/car/rail/hotel)', []

    travel_type = TRAVEL_TYPE_MAP.get(type_raw.strip().lower())
    if travel_type is None:
        return None, f"unknown travel type '{type_raw}' — expected flight, car, rail, or hotel", []

    date_str = resolve(row, *DATE_COL)
    if not date_str:
        return None, 'missing date column', []
    try:
        depart_date = parse_date(date_str)
    except ValueError:
        return None, f"invalid date '{date_str}'", []

    if travel_type == 'hotel':
        co2e_kg, original_value, original_unit, desc = _calc_hotel(row, row_num, row_warnings)
    else:
        co2e_kg, original_value, original_unit, desc = _calc_transport(row, travel_type, row_num, row_warnings)
        if co2e_kg is None:
            return None, desc, []

    origin = resolve(row, *ORIGIN_COL)
    dest   = resolve(row, *DEST_COL)

    return {
        'row': row_num, 'raw': row,
        'scope': 3, 'source': 'travel',
        'activity_date': depart_date,
        'description': desc,
        'location': f"{origin} -> {dest}" if origin or dest else travel_type,
        'original_value': float(original_value), 'original_unit': original_unit,
        'normalized_value': float(original_value), 'normalized_unit': original_unit,
        'co2e_kg': float(co2e_kg),
        'warnings': row_warnings,
    }, None, row_warnings


def _calc_hotel(row, row_num, row_warnings):
    nights = 1
    try:
        depart_str = resolve(row, *DATE_COL)
        ret_str    = resolve(row, *RETURN_COL)
        if depart_str and ret_str:
            nights = max(1, (parse_date(ret_str) - parse_date(depart_str)).days)
    except (ValueError, TypeError):
        row_warnings.append({'row': row_num, 'msg': 'could not compute hotel nights, defaulting to 1'})

    dest = resolve(row, *DEST_COL) or resolve(row, *ORIGIN_COL) or 'unknown'
    co2e = HOTEL_FACTOR_PER_NIGHT * Decimal(str(nights))
    return co2e, nights, 'nights', f"hotel stay {nights} night(s) in {dest}"


def _calc_transport(row, travel_type, row_num, row_warnings):
    distance_km = None

    dist_str = resolve(row, *DISTANCE_COL)
    if dist_str:
        try:
            distance_km = Decimal(dist_str.replace(',', '.'))
        except Exception:
            row_warnings.append({'row': row_num, 'msg': f"invalid distance '{dist_str}', will try alternatives"})

    if distance_km is None:
        miles_str = resolve(row, *MILES_COL)
        if miles_str:
            try:
                distance_km = Decimal(miles_str.replace(',', '.')) * Decimal('1.60934')
                row_warnings.append({'row': row_num, 'msg': f"converted {miles_str} miles to {float(distance_km):.1f} km"})
            except Exception:
                pass

    if distance_km is None and travel_type == 'flight':
        origin = resolve(row, *ORIGIN_COL).upper()
        dest   = resolve(row, *DEST_COL).upper()
        if origin and dest:
            hav = _haversine(origin, dest)
            if hav:
                distance_km = Decimal(str(hav))
                row_warnings.append({'row': row_num, 'msg': f"distance computed via haversine {origin}->{dest}: {hav:.0f} km"})
            else:
                return None, None, None, f"unknown airport codes '{origin}'/'{dest}' — add IATA codes or provide distance_km"
        else:
            return None, None, None, 'flight row missing origin/destination and no distance provided'

    if distance_km is None:
        return None, None, None, f"no distance available for {travel_type} trip"

    origin = resolve(row, *ORIGIN_COL)
    dest   = resolve(row, *DEST_COL)
    co2e   = distance_km * EMISSION_FACTORS[travel_type]
    return co2e, distance_km, 'km', f"{travel_type} {origin} to {dest}".strip()


def _haversine(a: str, b: str):
    if a not in AIRPORT_COORDS or b not in AIRPORT_COORDS:
        return None
    lat1, lon1 = AIRPORT_COORDS[a]
    lat2, lon2 = AIRPORT_COORDS[b]
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a_ = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a_), math.sqrt(1 - a_))
