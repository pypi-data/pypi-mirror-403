"""
Medical data validators.

Provides validation functions for:
- Vital signs (heart rate, blood pressure, temperature, etc.)
- Medication dosages
- CID-10 codes (ICD-10)
- CRM (Conselho Regional de Medicina) numbers
- Medical units and measurements
"""

import re
from dataclasses import dataclass

# =============================================================================
# Vital Signs Ranges
# =============================================================================


@dataclass
class VitalSignRange:
    """Range definition for vital signs."""

    name: str
    unit: str
    normal_min: float
    normal_max: float
    critical_min: float
    critical_max: float
    absolute_min: float = 0
    absolute_max: float = float("inf")


# Standard vital sign ranges for adults
VITAL_SIGN_RANGES = {
    "heart_rate": VitalSignRange(
        name="Heart Rate",
        unit="bpm",
        normal_min=60,
        normal_max=100,
        critical_min=40,
        critical_max=150,
        absolute_min=0,
        absolute_max=300,
    ),
    "systolic_bp": VitalSignRange(
        name="Systolic Blood Pressure",
        unit="mmHg",
        normal_min=90,
        normal_max=120,
        critical_min=70,
        critical_max=180,
        absolute_min=0,
        absolute_max=300,
    ),
    "diastolic_bp": VitalSignRange(
        name="Diastolic Blood Pressure",
        unit="mmHg",
        normal_min=60,
        normal_max=80,
        critical_min=40,
        critical_max=120,
        absolute_min=0,
        absolute_max=200,
    ),
    "temperature": VitalSignRange(
        name="Body Temperature",
        unit="°C",
        normal_min=36.0,
        normal_max=37.5,
        critical_min=34.0,
        critical_max=41.0,
        absolute_min=25.0,
        absolute_max=45.0,
    ),
    "respiratory_rate": VitalSignRange(
        name="Respiratory Rate",
        unit="rpm",
        normal_min=12,
        normal_max=20,
        critical_min=8,
        critical_max=30,
        absolute_min=0,
        absolute_max=60,
    ),
    "oxygen_saturation": VitalSignRange(
        name="Oxygen Saturation",
        unit="%",
        normal_min=95,
        normal_max=100,
        critical_min=88,
        critical_max=100,
        absolute_min=0,
        absolute_max=100,
    ),
    "glucose": VitalSignRange(
        name="Blood Glucose",
        unit="mg/dL",
        normal_min=70,
        normal_max=100,
        critical_min=50,
        critical_max=250,
        absolute_min=0,
        absolute_max=1000,
    ),
}


def validate_vital_sign(
    value: float, vital_type: str, check_critical: bool = True
) -> tuple[bool, str | None]:
    """
    Validate a vital sign value.

    Args:
        value: The vital sign value
        vital_type: Type of vital sign (heart_rate, systolic_bp, etc.)
        check_critical: If True, also checks if value is in critical range

    Returns:
        Tuple of (is_valid, status_message)
        Status can be: "normal", "low", "high", "critical_low", "critical_high", "invalid"

    Example:
        >>> validate_vital_sign(75, "heart_rate")
        (True, "normal")
        >>> validate_vital_sign(180, "systolic_bp")
        (True, "critical_high")
    """
    if vital_type not in VITAL_SIGN_RANGES:
        return False, f"Unknown vital sign type: {vital_type}"

    vsr = VITAL_SIGN_RANGES[vital_type]

    # Check absolute bounds
    if value < vsr.absolute_min or value > vsr.absolute_max:
        return False, "invalid"

    # Check critical ranges
    if check_critical:
        if value < vsr.critical_min:
            return True, "critical_low"
        if value > vsr.critical_max:
            return True, "critical_high"

    # Check normal ranges
    if value < vsr.normal_min:
        return True, "low"
    if value > vsr.normal_max:
        return True, "high"

    return True, "normal"


def validate_blood_pressure(systolic: float, diastolic: float) -> tuple[bool, str]:
    """
    Validate blood pressure reading.

    Args:
        systolic: Systolic pressure (mmHg)
        diastolic: Diastolic pressure (mmHg)

    Returns:
        Tuple of (is_valid, classification)
        Classification: "normal", "elevated", "hypertension_stage_1",
                       "hypertension_stage_2", "hypertensive_crisis", "hypotension"

    Example:
        >>> validate_blood_pressure(120, 80)
        (True, "normal")
    """
    # Diastolic should not be higher than systolic
    if diastolic >= systolic:
        return False, "invalid"

    # Check absolute bounds
    if systolic < 0 or systolic > 300 or diastolic < 0 or diastolic > 200:
        return False, "invalid"

    # Classifications based on AHA guidelines
    if systolic < 90 or diastolic < 60:
        return True, "hypotension"
    elif systolic < 120 and diastolic < 80:
        return True, "normal"
    elif systolic < 130 and diastolic < 80:
        return True, "elevated"
    elif systolic < 140 or diastolic < 90:
        return True, "hypertension_stage_1"
    elif systolic < 180 and diastolic < 120:
        return True, "hypertension_stage_2"
    else:
        return True, "hypertensive_crisis"


def validate_temperature(value: float, unit: str = "celsius") -> tuple[bool, str]:
    """
    Validate body temperature.

    Args:
        value: Temperature value
        unit: "celsius" or "fahrenheit"

    Returns:
        Tuple of (is_valid, classification)
        Classification: "hypothermia", "low", "normal", "low_fever",
                       "moderate_fever", "high_fever", "hyperpyrexia"
    """
    # Convert to Celsius if needed
    if unit.lower() in ("fahrenheit", "f"):
        value = (value - 32) * 5 / 9

    # Check absolute bounds
    if value < 25 or value > 45:
        return False, "invalid"

    if value < 35.0:
        return True, "hypothermia"
    elif value < 36.0:
        return True, "low"
    elif value <= 37.5:
        return True, "normal"
    elif value <= 38.0:
        return True, "low_fever"
    elif value <= 39.0:
        return True, "moderate_fever"
    elif value <= 41.0:
        return True, "high_fever"
    else:
        return True, "hyperpyrexia"


# =============================================================================
# CID-10 (ICD-10) Validation
# =============================================================================

CID10_REGEX = re.compile(r"^[A-TV-Z]\d{2}(\.\d{1,2})?$", re.IGNORECASE)

# CID-10 chapter ranges
CID10_CHAPTERS = {
    "A00-B99": "Infectious and parasitic diseases",
    "C00-D48": "Neoplasms",
    "D50-D89": "Blood diseases",
    "E00-E90": "Endocrine, nutritional and metabolic diseases",
    "F00-F99": "Mental and behavioural disorders",
    "G00-G99": "Nervous system diseases",
    "H00-H59": "Eye diseases",
    "H60-H95": "Ear diseases",
    "I00-I99": "Circulatory system diseases",
    "J00-J99": "Respiratory system diseases",
    "K00-K93": "Digestive system diseases",
    "L00-L99": "Skin diseases",
    "M00-M99": "Musculoskeletal diseases",
    "N00-N99": "Genitourinary system diseases",
    "O00-O99": "Pregnancy and childbirth",
    "P00-P96": "Perinatal conditions",
    "Q00-Q99": "Congenital malformations",
    "R00-R99": "Symptoms and signs",
    "S00-T98": "Injuries and poisoning",
    "V01-Y98": "External causes",
    "Z00-Z99": "Health status factors",
}


def validate_cid10(code: str) -> bool:
    """
    Validate CID-10 (ICD-10) code format.

    Args:
        code: CID-10 code (e.g., "A01.1", "J18", "M54.5")

    Returns:
        True if valid format, False otherwise

    Example:
        >>> validate_cid10("J18")
        True
        >>> validate_cid10("J18.0")
        True
        >>> validate_cid10("invalid")
        False
    """
    if not code or not isinstance(code, str):
        return False

    code = code.strip().upper()
    return bool(CID10_REGEX.match(code))


def get_cid10_chapter(code: str) -> str | None:
    """
    Get the chapter name for a CID-10 code.

    Args:
        code: CID-10 code

    Returns:
        Chapter description or None if invalid
    """
    if not validate_cid10(code):
        return None

    code = code.upper()
    letter = code[0]
    number = int(code[1:3])

    # Map letter + number to chapter
    for range_str, description in CID10_CHAPTERS.items():
        start, end = range_str.split("-")
        start_letter, start_num = start[0], int(start[1:])
        end_letter, end_num = end[0], int(end[1:])

        # Check if code falls within chapter range
        if start_letter <= letter <= end_letter:
            if letter == start_letter and number < start_num:
                continue
            if letter == end_letter and number > end_num:
                continue
            return description

    return None


# Alias for backwards compatibility
is_valid_cid10 = validate_cid10


# =============================================================================
# CRM Validation
# =============================================================================


def clean_crm(crm: str) -> str:
    """Remove all non-alphanumeric characters from CRM."""
    if crm is None:
        return ""
    return re.sub(r"[^a-zA-Z0-9]", "", str(crm))


def validate_crm(crm: str, uf: str | None = None) -> bool:
    """
    Validate CRM (Conselho Regional de Medicina) number.

    CRM format: 1-6 digits followed by optional UF (e.g., "12345-MG", "123456SP")

    Args:
        crm: CRM number (with or without UF)
        uf: Expected UF (if provided, validates against it)

    Returns:
        True if valid format, False otherwise

    Example:
        >>> validate_crm("12345-MG")
        True
        >>> validate_crm("123456", uf="SP")
        True
    """
    from .brazil import VALID_UFS

    if not crm or not isinstance(crm, str):
        return False

    # Clean and parse
    cleaned = clean_crm(crm).upper()

    # Extract UF if present (last 2 characters if alphabetic)
    if len(cleaned) >= 3 and cleaned[-2:].isalpha():
        extracted_uf = cleaned[-2:]
        number = cleaned[:-2]
    else:
        extracted_uf = None
        number = cleaned

    # Validate number (1-6 digits)
    if not number.isdigit() or len(number) < 1 or len(number) > 6:
        return False

    # Validate UF if extracted
    if extracted_uf and extracted_uf not in VALID_UFS:
        return False

    # Check against expected UF if provided
    if uf:
        uf = uf.upper()
        if uf not in VALID_UFS:
            return False
        if extracted_uf and extracted_uf != uf:
            return False

    return True


def format_crm(crm: str, uf: str | None = None) -> str:
    """
    Format CRM number.

    Args:
        crm: CRM number
        uf: UF to append (if not already present)

    Returns:
        Formatted CRM (e.g., "CRM/MG 12345")
    """
    cleaned = clean_crm(crm).upper()

    # Extract UF if present
    if len(cleaned) >= 3 and cleaned[-2:].isalpha():
        extracted_uf = cleaned[-2:]
        number = cleaned[:-2]
    else:
        extracted_uf = uf.upper() if uf else None
        number = cleaned

    if extracted_uf:
        return f"CRM/{extracted_uf} {number}"
    return f"CRM {number}"


# Alias for backwards compatibility
is_valid_crm = validate_crm


# =============================================================================
# Medication Validation
# =============================================================================

# Common medication units
MEDICATION_UNITS = frozenset(
    {
        "mg",
        "g",
        "mcg",
        "kg",  # Mass
        "ml",
        "l",
        "cc",  # Volume
        "ui",
        "iu",  # International units
        "meq",
        "mmol",
        "mol",  # Moles
        "gtt",
        "gotas",
        "drops",  # Drops
        "cp",
        "comp",
        "caps",
        "capsule",  # Pills
        "amp",
        "ampola",  # Ampoule
        "fr",
        "frasco",  # Flask
        "tb",
        "tubo",  # Tube
        "%",  # Percentage
    }
)


def validate_medication_dosage(
    dosage: str, max_value: float | None = None
) -> tuple[bool, dict | None]:
    """
    Validate and parse medication dosage string.

    Args:
        dosage: Dosage string (e.g., "500mg", "10 ml", "2 comprimidos")
        max_value: Maximum allowed numeric value

    Returns:
        Tuple of (is_valid, parsed_data)
        parsed_data contains: {"value": float, "unit": str, "original": str}

    Example:
        >>> validate_medication_dosage("500mg")
        (True, {"value": 500.0, "unit": "mg", "original": "500mg"})
    """
    if not dosage or not isinstance(dosage, str):
        return False, None

    dosage = dosage.strip().lower()

    # Pattern: number (with optional decimal) followed by unit
    pattern = r"^(\d+(?:[.,]\d+)?)\s*([a-z%]+)$"
    match = re.match(pattern, dosage)

    if not match:
        return False, None

    value_str, unit = match.groups()
    value = float(value_str.replace(",", "."))

    # Validate unit
    if unit not in MEDICATION_UNITS:
        return False, None

    # Validate max value
    if max_value is not None and value > max_value:
        return False, None

    return True, {"value": value, "unit": unit, "original": dosage}


def validate_medication_frequency(frequency: str) -> tuple[bool, dict | None]:
    """
    Validate medication frequency string.

    Args:
        frequency: Frequency string (e.g., "8/8h", "12/12h", "1x ao dia")

    Returns:
        Tuple of (is_valid, parsed_data)
        parsed_data contains: {"times_per_day": int, "interval_hours": float}

    Example:
        >>> validate_medication_frequency("8/8h")
        (True, {"times_per_day": 3, "interval_hours": 8.0})
    """
    if not frequency or not isinstance(frequency, str):
        return False, None

    frequency = frequency.strip().lower()

    # Pattern: X/Xh (e.g., 8/8h, 12/12h, 6/6h)
    pattern1 = r"^(\d+)/(\d+)\s*h$"
    match = re.match(pattern1, frequency)
    if match:
        interval = float(match.group(1))
        if interval > 0 and interval <= 24:
            times_per_day = int(24 / interval)
            return True, {"times_per_day": times_per_day, "interval_hours": interval}

    # Pattern: Xx ao dia (e.g., 1x ao dia, 2x ao dia)
    pattern2 = r"^(\d+)\s*x?\s*(?:ao\s*dia|por\s*dia|/dia)$"
    match = re.match(pattern2, frequency)
    if match:
        times = int(match.group(1))
        if times > 0 and times <= 24:
            interval = 24 / times
            return True, {"times_per_day": times, "interval_hours": interval}

    return False, None


# =============================================================================
# BMI Calculation and Validation
# =============================================================================


def calculate_bmi(weight_kg: float, height_cm: float) -> float | None:
    """
    Calculate Body Mass Index (BMI).

    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters

    Returns:
        BMI value or None if invalid inputs
    """
    if weight_kg <= 0 or height_cm <= 0:
        return None

    height_m = height_cm / 100
    return round(weight_kg / (height_m**2), 2)


def classify_bmi(bmi: float) -> str | None:
    """
    Classify BMI according to WHO categories.

    Args:
        bmi: BMI value

    Returns:
        Classification string or None if invalid
    """
    if bmi is None or bmi <= 0:
        return None

    if bmi < 16:
        return "severe_underweight"
    elif bmi < 17:
        return "moderate_underweight"
    elif bmi < 18.5:
        return "mild_underweight"
    elif bmi < 25:
        return "normal"
    elif bmi < 30:
        return "overweight"
    elif bmi < 35:
        return "obese_class_1"
    elif bmi < 40:
        return "obese_class_2"
    else:
        return "obese_class_3"


def validate_weight(weight_kg: float) -> bool:
    """Validate weight in kilograms (reasonable adult range)."""
    return 2 <= weight_kg <= 500


def validate_height(height_cm: float) -> bool:
    """Validate height in centimeters (reasonable adult range)."""
    return 50 <= height_cm <= 280
