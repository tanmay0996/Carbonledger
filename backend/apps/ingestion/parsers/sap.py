import csv
import io
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

PLANT_LOCATIONS = {
    'PLANT_1000': 'Hamburg, DE',
    'PLANT_2000': 'Munich, DE',
    'PLANT_3000': 'Berlin, DE',
    'PLANT_4000': 'Frankfurt, DE',
    'PLANT_5000': 'Stuttgart, DE',
}

MATERIAL_FUEL_TYPE = {
    'MAT-DSL-001': 'diesel',
    'MAT-PET-002': 'petrol',
    'MAT-HFO-003': 'heavy_fuel_oil',
    'MAT-LPG-004': 'lpg',
}

# kgCO2e per liter for each fuel type
EMISSION_FACTORS = {
    'diesel': Decimal('2.6391'),
    'petrol': Decimal('2.3101'),
    'heavy_fuel_oil': Decimal('3.1867'),
    'lpg': Decimal('1.5480'),
}

# Conversion to liters
UNIT_TO_LITERS = {
    'L': Decimal('1.0'),
    'GAL': Decimal('3.78541'),
    'KG': None,  # KG conversion is fuel-type specific
}

# KG to liters for fuels sold by weight
KG_TO_LITERS = {
    'heavy_fuel_oil': Decimal('1.010'),  # approx density: 1 L HFO ~ 0.99 kg, so 1 kg ~ 1.010 L
    'lpg': Decimal('1.960'),             # 1 kg LPG ~ 1.96 L
    'diesel': Decimal('1.176'),
    'petrol': Decimal('1.351'),
}

REQUIRED_FIELDS = ['Buchungskreis', 'Werk', 'Materialnummer', 'Menge', 'Einheit', 'Buchungsdatum']


def parse(file_content: str) -> dict:
    success = []
    failed = []
    warnings = []

    reader = csv.DictReader(io.StringIO(file_content), delimiter=';')

    for row_num, row in enumerate(reader, start=2):
        raw = dict(row)
        result = _parse_row(row_num, raw)
        if result is None:
            failed.append({'row': row_num, 'raw': raw, 'error': _last_error})
        else:
            if result.get('warnings'):
                warnings.extend(result['warnings'])
            success.append(result)

    return {'success': success, 'failed': failed, 'warnings': warnings}


_last_error = ''


def _parse_row(row_num: int, row: dict) -> dict | None:
    global _last_error

    missing = [f for f in REQUIRED_FIELDS if not row.get(f, '').strip()]
    if missing:
        _last_error = f"missing required fields: {missing}"
        return None

    plant = row['Werk'].strip()
    material = row['Materialnummer'].strip()
    unit = row['Einheit'].strip().upper()
    raw_qty_str = row['Menge'].strip().replace(',', '.')
    date_str = row['Buchungsdatum'].strip()

    try:
        raw_qty = Decimal(raw_qty_str)
    except InvalidOperation:
        _last_error = f"invalid quantity '{raw_qty_str}'"
        return None

    try:
        activity_date = datetime.strptime(date_str, '%Y%m%d').date()
    except ValueError:
        _last_error = f"invalid date '{date_str}'"
        return None

    fuel_type = MATERIAL_FUEL_TYPE.get(material)
    if fuel_type is None:
        _last_error = f"unknown material code '{material}'"
        return None

    if unit not in UNIT_TO_LITERS:
        _last_error = f"unsupported unit '{unit}'"
        return None

    if unit == 'KG':
        kg_factor = KG_TO_LITERS.get(fuel_type)
        if kg_factor is None:
            _last_error = f"no KG->L factor for fuel '{fuel_type}'"
            return None
        liters = raw_qty * kg_factor
    else:
        liters = raw_qty * UNIT_TO_LITERS[unit]

    ef = EMISSION_FACTORS[fuel_type]
    co2e_kg = liters * ef

    row_warnings = []
    location = PLANT_LOCATIONS.get(plant)
    if location is None:
        location = plant
        row_warnings.append({'row': row_num, 'msg': f"unknown plant code '{plant}', using code as location"})

    return {
        'row': row_num,
        'raw': row,
        'scope': 1,
        'source': 'sap',
        'activity_date': activity_date,
        'description': f"{MATERIAL_FUEL_TYPE.get(material, material)} consumption",
        'location': location,
        'original_value': float(raw_qty),
        'original_unit': unit,
        'normalized_value': float(liters),
        'normalized_unit': 'L',
        'co2e_kg': float(co2e_kg),
        'warnings': row_warnings,
    }
