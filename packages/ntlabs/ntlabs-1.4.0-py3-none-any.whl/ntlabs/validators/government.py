"""
Government data validators.

Provides validation functions for:
- IBGE codes (municipalities, states)
- Government contract data
- Portal da Transparência data
- Public bidding (licitações)
"""

import re
from datetime import date

# =============================================================================
# IBGE Code Validation
# =============================================================================


def validate_ibge_state_code(code: int) -> bool:
    """
    Validate IBGE state code.

    Args:
        code: IBGE state code (2 digits)

    Returns:
        True if valid state code, False otherwise

    Example:
        >>> validate_ibge_state_code(31)  # Minas Gerais
        True
        >>> validate_ibge_state_code(99)
        False
    """
    # Valid IBGE state codes
    valid_codes = {
        11,
        12,
        13,
        14,
        15,
        16,
        17,  # North
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,  # Northeast
        31,
        32,
        33,
        35,  # Southeast
        41,
        42,
        43,  # South
        50,
        51,
        52,
        53,  # Central-West
    }
    return code in valid_codes


def validate_ibge_municipality_code(code: int) -> bool:
    """
    Validate IBGE municipality code.

    Municipality codes have 7 digits:
    - First 2: state code
    - Remaining 5: municipality identifier

    Args:
        code: IBGE municipality code (7 digits)

    Returns:
        True if valid format, False otherwise

    Example:
        >>> validate_ibge_municipality_code(3106200)  # Belo Horizonte
        True
    """
    if not isinstance(code, int):
        try:
            code = int(code)
        except (ValueError, TypeError):
            return False

    # Must be 7 digits
    if code < 1000000 or code > 9999999:
        return False

    # Extract state code (first 2 digits)
    state_code = code // 100000

    return validate_ibge_state_code(state_code)


def get_state_from_municipality_code(code: int) -> int | None:
    """
    Extract state code from municipality code.

    Args:
        code: IBGE municipality code

    Returns:
        State code or None if invalid
    """
    if not validate_ibge_municipality_code(code):
        return None
    return code // 100000


# Alias for backwards compatibility
is_valid_ibge_code = validate_ibge_municipality_code


# =============================================================================
# Government Contract Validation
# =============================================================================

# Contract number patterns (various formats used by different agencies)
CONTRACT_PATTERNS = [
    r"^\d{1,4}/\d{4}$",  # 123/2024
    r"^\d{2}\.\d{3}/\d{4}$",  # 01.234/2024
    r"^CT[.-]?\d{4,}/\d{4}$",  # CT-1234/2024
    r"^CONTRATO\s+N[°º]?\s*\d+/\d{4}$",  # CONTRATO Nº 123/2024
]


def validate_contract_number(number: str) -> bool:
    """
    Validate government contract number format.

    Args:
        number: Contract number string

    Returns:
        True if matches common contract number patterns

    Example:
        >>> validate_contract_number("123/2024")
        True
        >>> validate_contract_number("CT-4567/2024")
        True
    """
    if not number or not isinstance(number, str):
        return False

    number = number.strip().upper()

    for pattern in CONTRACT_PATTERNS:
        if re.match(pattern, number, re.IGNORECASE):
            return True

    return False


def validate_contract_value(
    value: float, min_value: float = 0, max_value: float | None = None
) -> tuple[bool, str | None]:
    """
    Validate contract value.

    Args:
        value: Contract value in BRL
        min_value: Minimum valid value
        max_value: Maximum valid value

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, (int, float)):
        return False, "Value must be numeric"

    if value < min_value:
        return False, f"Value must be at least {min_value}"

    if max_value is not None and value > max_value:
        return False, f"Value exceeds maximum of {max_value}"

    # Check for suspiciously round values (potential red flag)
    if value >= 10000 and value % 10000 == 0:
        return True, "warning: suspiciously round value"

    return True, None


def validate_contract_dates(
    start_date: date,
    end_date: date,
    signature_date: date | None = None,
    max_duration_days: int = 1825,  # 5 years default
) -> tuple[bool, str | None]:
    """
    Validate contract date consistency.

    Args:
        start_date: Contract start date
        end_date: Contract end date
        signature_date: Contract signature date (optional)
        max_duration_days: Maximum allowed contract duration

    Returns:
        Tuple of (is_valid, error_message)
    """
    # End must be after start
    if end_date <= start_date:
        return False, "End date must be after start date"

    # Check duration
    duration = (end_date - start_date).days
    if duration > max_duration_days:
        return False, f"Contract duration exceeds {max_duration_days} days"

    # Signature should be before or on start date
    if signature_date:
        if signature_date > start_date:
            return False, "Signature date should be before start date"

        # Signature shouldn't be too far in the past
        days_before_start = (start_date - signature_date).days
        if days_before_start > 365:
            return True, "warning: signature date is over a year before start"

    return True, None


# =============================================================================
# Bidding Process (Licitação) Validation
# =============================================================================

# Bidding modalities
BIDDING_MODALITIES = {
    "CONCORRENCIA": "Concorrência",
    "TOMADA_PRECOS": "Tomada de Preços",
    "CONVITE": "Convite",
    "CONCURSO": "Concurso",
    "LEILAO": "Leilão",
    "PREGAO_ELETRONICO": "Pregão Eletrônico",
    "PREGAO_PRESENCIAL": "Pregão Presencial",
    "RDC": "Regime Diferenciado de Contratação",
    "DISPENSA": "Dispensa de Licitação",
    "INEXIGIBILIDADE": "Inexigibilidade",
}

# Value thresholds for bidding modalities (Lei 14.133/2021)
BIDDING_THRESHOLDS = {
    "DISPENSA_OBRAS": 100000.00,
    "DISPENSA_SERVICOS": 50000.00,
    "CONVITE_OBRAS": 330000.00,
    "CONVITE_SERVICOS": 176000.00,
    "TOMADA_PRECOS_OBRAS": 3300000.00,
    "TOMADA_PRECOS_SERVICOS": 1430000.00,
}


def validate_bidding_modality(modality: str) -> bool:
    """
    Validate bidding modality.

    Args:
        modality: Bidding modality code or name

    Returns:
        True if valid modality

    Example:
        >>> validate_bidding_modality("PREGAO_ELETRONICO")
        True
    """
    if not modality:
        return False

    modality = modality.upper().replace(" ", "_").replace("-", "_")
    return modality in BIDDING_MODALITIES


def get_bidding_modality_name(modality: str) -> str | None:
    """
    Get friendly name for bidding modality.

    Args:
        modality: Bidding modality code

    Returns:
        Friendly name or None if invalid
    """
    if not modality:
        return None

    modality = modality.upper().replace(" ", "_").replace("-", "_")
    return BIDDING_MODALITIES.get(modality)


def validate_bidding_value_modality(
    value: float, modality: str, contract_type: str = "servicos"
) -> tuple[bool, str | None]:
    """
    Validate if bidding value is appropriate for the modality.

    Args:
        value: Contract value in BRL
        modality: Bidding modality
        contract_type: "obras" or "servicos"

    Returns:
        Tuple of (is_valid, warning_message)

    Example:
        >>> validate_bidding_value_modality(1000000, "CONVITE", "obras")
        (False, "Value exceeds limit for Convite")
    """
    modality = modality.upper().replace(" ", "_").replace("-", "_")
    contract_type = contract_type.lower()

    if contract_type not in ("obras", "servicos"):
        contract_type = "servicos"

    # Check dispensa threshold
    dispensa_key = f"DISPENSA_{contract_type.upper()}"
    if value <= BIDDING_THRESHOLDS.get(dispensa_key, 0):
        if modality not in ("DISPENSA", "INEXIGIBILIDADE"):
            return True, "Could use dispensa for this value"

    # Check convite threshold
    convite_key = f"CONVITE_{contract_type.upper()}"
    if modality == "CONVITE" and value > BIDDING_THRESHOLDS.get(convite_key, 0):
        return False, "Value exceeds limit for Convite"

    # Check tomada de preços threshold
    tp_key = f"TOMADA_PRECOS_{contract_type.upper()}"
    if modality == "TOMADA_PRECOS" and value > BIDDING_THRESHOLDS.get(tp_key, 0):
        return False, "Value exceeds limit for Tomada de Preços"

    return True, None


# =============================================================================
# CNAE (Economic Activity) Validation
# =============================================================================

CNAE_REGEX = re.compile(r"^\d{4}-?\d/?\d{2}$")


def clean_cnae(cnae: str) -> str:
    """Remove formatting from CNAE code."""
    if cnae is None:
        return ""
    return re.sub(r"[^0-9]", "", str(cnae))


def validate_cnae(cnae: str) -> bool:
    """
    Validate CNAE (Classificação Nacional de Atividades Econômicas) code.

    Args:
        cnae: CNAE code (e.g., "6201-5/00", "62015/00", "6201500")

    Returns:
        True if valid format (7 digits), False otherwise

    Example:
        >>> validate_cnae("6201-5/00")
        True
    """
    cleaned = clean_cnae(cnae)
    return len(cleaned) == 7 and cleaned.isdigit()


def format_cnae(cnae: str) -> str:
    """
    Format CNAE as XXXX-X/XX.

    Args:
        cnae: CNAE code (digits only or formatted)

    Returns:
        Formatted CNAE string
    """
    cleaned = clean_cnae(cnae)
    if len(cleaned) != 7:
        return cnae
    return f"{cleaned[:4]}-{cleaned[4]}/{cleaned[5:]}"


# Alias for backwards compatibility
is_valid_cnae = validate_cnae


# =============================================================================
# Anomaly Detection Helpers
# =============================================================================


def check_value_anomaly(
    value: float, mean: float, std_dev: float, threshold: float = 2.0
) -> tuple[bool, str | None]:
    """
    Check if a value is anomalous compared to historical data.

    Uses Z-score method.

    Args:
        value: Value to check
        mean: Historical mean
        std_dev: Historical standard deviation
        threshold: Z-score threshold (default 2.0 = ~95% confidence)

    Returns:
        Tuple of (is_anomalous, description)
    """
    if std_dev == 0:
        return value != mean, "exact match required" if value != mean else None

    z_score = abs(value - mean) / std_dev

    if z_score > threshold:
        direction = "above" if value > mean else "below"
        return True, f"Value is {z_score:.2f} std devs {direction} mean"

    return False, None


def check_date_anomaly(
    event_date: date, expected_date: date, tolerance_days: int = 30
) -> tuple[bool, str | None]:
    """
    Check if a date is anomalous compared to expected date.

    Args:
        event_date: Actual event date
        expected_date: Expected date
        tolerance_days: Allowed variance in days

    Returns:
        Tuple of (is_anomalous, description)
    """
    diff = abs((event_date - expected_date).days)

    if diff > tolerance_days:
        direction = "after" if event_date > expected_date else "before"
        return True, f"Date is {diff} days {direction} expected"

    return False, None


def check_supplier_concentration(
    supplier_share: float, threshold: float = 0.5
) -> tuple[bool, str | None]:
    """
    Check if supplier concentration is suspicious.

    Args:
        supplier_share: Percentage of contracts held by supplier (0-1)
        threshold: Maximum acceptable share

    Returns:
        Tuple of (is_suspicious, description)
    """
    if supplier_share > threshold:
        return True, f"Supplier has {supplier_share*100:.1f}% of contracts"
    return False, None
