import logging
from decimal import Decimal, InvalidOperation
from .utils import resolve, parse_date, make_reader, detect_delimiter

logger = logging.getLogger(__name__)

PLANT_LOCATIONS = {
    'PLANT_1000': 'Hamburg, DE',   'PLANT_2000': 'Munich, DE',
    'PLANT_3000': 'Berlin, DE',    'PLANT_4000': 'Frankfurt, DE',
    'PLANT_5000': 'Stuttgart, DE',
}

MATERIAL_FUEL_TYPE = {
    'MAT-DSL-001': 'diesel', 'MAT-PET-002': 'petrol',
    'MAT-HFO-003': 'heavy_fuel_oil', 'MAT-LPG-004': 'lpg',
}

FUEL_NAME_MAP = {
    'diesel': 'diesel', 'gasoil': 'diesel', 'gas oil': 'diesel',
    'petrol': 'petrol', 'gasoline': 'petrol', 'benzin': 'petrol', 'benzine': 'petrol',
    'heavy_fuel_oil': 'heavy_fuel_oil', 'hfo': 'heavy_fuel_oil',
    'fuel oil': 'heavy_fuel_oil', 'heavy fuel oil': 'heavy_fuel_oil',
    'schweröl': 'heavy_fuel_oil', 'schweroel': 'heavy_fuel_oil',
    'lpg': 'lpg', 'flüssiggas': 'lpg', 'flussiggas': 'lpg',
    'liquefied petroleum gas': 'lpg', 'propane': 'lpg', 'butane': 'lpg',
    'natural gas': 'lpg', 'cng': 'lpg',
}

EMISSION_FACTORS = {
    'diesel': Decimal('2.6391'), 'petrol': Decimal('2.3101'),
    'heavy_fuel_oil': Decimal('3.1867'), 'lpg': Decimal('1.5480'),
}

UNIT_TO_LITERS = {'L': Decimal('1.0'), 'GAL': Decimal('3.78541'), 'KG': None}

UNIT_NORMALIZE = {
    'l': 'L', 'liter': 'L', 'litre': 'L', 'liters': 'L', 'litres': 'L', 'ltr': 'L',
    'kg': 'KG', 'kilogram': 'KG', 'kilograms': 'KG', 'kgs': 'KG',
    'gal': 'GAL', 'gallon': 'GAL', 'gallons': 'GAL', 'us gal': 'GAL',
}

KG_TO_LITERS = {
    'heavy_fuel_oil': Decimal('1.010'), 'lpg': Decimal('1.960'),
    'diesel': Decimal('1.176'), 'petrol': Decimal('1.351'),
}

# German + English column aliases
COMPANY_COL  = ['Buchungskreis', 'company_code', 'company', 'client', 'buchungskreis']
PLANT_COL    = ['Werk', 'plant', 'werk', 'site', 'location', 'facility', 'plant_code', 'plant_id']
MATERIAL_COL = ['Materialnummer', 'material', 'material_number', 'material_code',
                'materialnummer', 'fuel', 'fuel_type', 'material_id', 'fuel_code']
DESC_COL     = ['Materialbezeichnung', 'description', 'material_description',
                'materialbezeichnung', 'name', 'fuel_name', 'material_name']
QTY_COL      = ['Menge', 'quantity', 'amount', 'menge', 'qty', 'volume',
                'consumption', 'usage', 'quantity_used']
UNIT_COL     = ['Einheit', 'unit', 'einheit', 'uom', 'unit_of_measure', 'units']
DATE_COL     = ['Buchungsdatum', 'date', 'posting_date', 'buchungsdatum',
                'activity_date', 'transaction_date', 'booking_date', 'period']


def parse(file_content: str) -> dict:
    success, failed, warnings = [], [], []
    delimiter = detect_delimiter(file_content)
    reader = make_reader(file_content, delimiter=delimiter)
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

    plant_raw    = resolve(row, *PLANT_COL)
    material_raw = resolve(row, *MATERIAL_COL)
    desc_raw     = resolve(row, *DESC_COL)
    qty_str      = resolve(row, *QTY_COL)
    unit_raw     = resolve(row, *UNIT_COL)
    date_str     = resolve(row, *DATE_COL)

    if not qty_str:
        return None, 'missing quantity column', []
    if not unit_raw:
        return None, 'missing unit column', []
    if not date_str:
        return None, 'missing date column', []
    if not (material_raw or desc_raw):
        return None, 'missing material/fuel type column', []

    try:
        raw_qty = Decimal(qty_str.replace(',', '.'))
    except InvalidOperation:
        return None, f"invalid quantity '{qty_str}'", []

    try:
        activity_date = parse_date(date_str)
    except ValueError as e:
        return None, str(e), []

    unit = UNIT_NORMALIZE.get(unit_raw.strip().lower(), unit_raw.strip().upper())
    if unit not in UNIT_TO_LITERS:
        return None, f"unsupported unit '{unit_raw}' — use L, KG, or GAL", []

    fuel_type = _resolve_fuel(material_raw, desc_raw)
    if fuel_type is None:
        tried = material_raw or desc_raw
        return None, f"unknown fuel type '{tried}' — use diesel, petrol, heavy_fuel_oil, or lpg", []

    if unit == 'KG':
        factor = KG_TO_LITERS.get(fuel_type)
        if not factor:
            return None, f"no KG→L conversion for '{fuel_type}'", []
        liters = raw_qty * factor
    else:
        liters = raw_qty * UNIT_TO_LITERS[unit]

    co2e_kg = liters * EMISSION_FACTORS[fuel_type]

    location = PLANT_LOCATIONS.get(plant_raw, plant_raw or 'Unknown')
    if plant_raw and plant_raw not in PLANT_LOCATIONS:
        row_warnings.append({'row': row_num, 'msg': f"unknown plant '{plant_raw}', using as-is"})

    return {
        'row': row_num, 'raw': row,
        'scope': 1, 'source': 'sap',
        'activity_date': activity_date,
        'description': f"{fuel_type.replace('_', ' ')} consumption",
        'location': location,
        'original_value': float(raw_qty), 'original_unit': unit,
        'normalized_value': float(liters), 'normalized_unit': 'L',
        'co2e_kg': float(co2e_kg),
        'warnings': row_warnings,
    }, None, row_warnings


def _resolve_fuel(material_raw: str, desc_raw: str) -> str | None:
    for val in [material_raw, desc_raw]:
        if not val:
            continue
        # exact material code lookup
        ft = MATERIAL_FUEL_TYPE.get(val.strip())
        if ft:
            return ft
        # fuzzy fuel name lookup
        ft = FUEL_NAME_MAP.get(val.strip().lower())
        if ft:
            return ft
        # partial match — "diesel 50ppm" → diesel
        lower = val.strip().lower()
        for name, mapped in FUEL_NAME_MAP.items():
            if name in lower:
                return mapped
    return None
