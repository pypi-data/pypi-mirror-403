"""
Brazilian document and data validators.

Provides validation, cleaning, and formatting functions for:
- CPF (Cadastro de Pessoas Físicas)
- CNPJ (Cadastro Nacional da Pessoa Jurídica)
- CEP (Código de Endereçamento Postal)
- UF (Unidade Federativa)
- Phone numbers (Brazilian format)
- PIS/PASEP
- CNS (Cartão Nacional de Saúde)

All validation functions follow these patterns:
- validate_*: Returns True/False
- clean_*: Removes formatting, returns digits only
- format_*: Adds proper formatting
- is_valid_*: Alias for validate_* (for backwards compatibility)
"""

import re

# Valid Brazilian states
VALID_UFS = frozenset(
    {
        "AC",
        "AL",
        "AP",
        "AM",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MT",
        "MS",
        "MG",
        "PA",
        "PB",
        "PR",
        "PE",
        "PI",
        "RJ",
        "RN",
        "RS",
        "RO",
        "RR",
        "SC",
        "SP",
        "SE",
        "TO",
    }
)

# State names mapping
UF_NAMES = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}

# IBGE state codes
UF_CODES = {
    "AC": 12,
    "AL": 27,
    "AP": 16,
    "AM": 13,
    "BA": 29,
    "CE": 23,
    "DF": 53,
    "ES": 32,
    "GO": 52,
    "MA": 21,
    "MT": 51,
    "MS": 50,
    "MG": 31,
    "PA": 15,
    "PB": 25,
    "PR": 41,
    "PE": 26,
    "PI": 22,
    "RJ": 33,
    "RN": 24,
    "RS": 43,
    "RO": 11,
    "RR": 14,
    "SC": 42,
    "SP": 35,
    "SE": 28,
    "TO": 17,
}


# =============================================================================
# CPF Functions
# =============================================================================


def clean_cpf(cpf: str) -> str:
    """Remove all non-digit characters from CPF."""
    if cpf is None:
        return ""
    return re.sub(r"\D", "", str(cpf))


def validate_cpf(cpf: str) -> bool:
    """
    Validate CPF using module 11 algorithm.

    Args:
        cpf: CPF string (with or without formatting)

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_cpf("123.456.789-09")
        True
        >>> validate_cpf("111.111.111-11")
        False
    """
    cpf = clean_cpf(cpf)

    # Must have exactly 11 digits
    if len(cpf) != 11:
        return False

    # Reject known invalid patterns (all same digits)
    if cpf == cpf[0] * 11:
        return False

    # Calculate first check digit
    total = sum(int(cpf[i]) * (10 - i) for i in range(9))
    remainder = total % 11
    digit1 = 0 if remainder < 2 else 11 - remainder

    if int(cpf[9]) != digit1:
        return False

    # Calculate second check digit
    total = sum(int(cpf[i]) * (11 - i) for i in range(10))
    remainder = total % 11
    digit2 = 0 if remainder < 2 else 11 - remainder

    return int(cpf[10]) == digit2


def format_cpf(cpf: str) -> str:
    """
    Format CPF as XXX.XXX.XXX-XX.

    Args:
        cpf: CPF string (digits only or formatted)

    Returns:
        Formatted CPF string

    Example:
        >>> format_cpf("12345678909")
        "123.456.789-09"
    """
    cpf = clean_cpf(cpf)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def generate_cpf() -> str:
    """
    Generate a valid random CPF (for testing purposes).

    Returns:
        Valid CPF string (formatted)
    """
    import random

    # Generate first 9 digits
    digits = [random.randint(0, 9) for _ in range(9)]

    # Ensure not all same digits
    while len(set(digits)) == 1:
        digits = [random.randint(0, 9) for _ in range(9)]

    # Calculate first check digit
    total = sum(d * (10 - i) for i, d in enumerate(digits))
    remainder = total % 11
    digit1 = 0 if remainder < 2 else 11 - remainder
    digits.append(digit1)

    # Calculate second check digit
    total = sum(d * (11 - i) for i, d in enumerate(digits))
    remainder = total % 11
    digit2 = 0 if remainder < 2 else 11 - remainder
    digits.append(digit2)

    return format_cpf("".join(map(str, digits)))


# Alias for backwards compatibility
is_valid_cpf = validate_cpf


# =============================================================================
# CNPJ Functions
# =============================================================================


def clean_cnpj(cnpj: str) -> str:
    """Remove all non-digit characters from CNPJ."""
    if cnpj is None:
        return ""
    return re.sub(r"\D", "", str(cnpj))


def validate_cnpj(cnpj: str) -> bool:
    """
    Validate CNPJ using module 11 algorithm.

    Args:
        cnpj: CNPJ string (with or without formatting)

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_cnpj("11.222.333/0001-81")
        True
        >>> validate_cnpj("11.111.111/1111-11")
        False
    """
    cnpj = clean_cnpj(cnpj)

    # Must have exactly 14 digits
    if len(cnpj) != 14:
        return False

    # Reject known invalid patterns
    if cnpj == cnpj[0] * 14:
        return False

    # Weights for first check digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(cnpj[i]) * weights1[i] for i in range(12))
    remainder = total % 11
    digit1 = 0 if remainder < 2 else 11 - remainder

    if int(cnpj[12]) != digit1:
        return False

    # Weights for second check digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(cnpj[i]) * weights2[i] for i in range(13))
    remainder = total % 11
    digit2 = 0 if remainder < 2 else 11 - remainder

    return int(cnpj[13]) == digit2


def format_cnpj(cnpj: str) -> str:
    """
    Format CNPJ as XX.XXX.XXX/XXXX-XX.

    Args:
        cnpj: CNPJ string (digits only or formatted)

    Returns:
        Formatted CNPJ string

    Example:
        >>> format_cnpj("11222333000181")
        "11.222.333/0001-81"
    """
    cnpj = clean_cnpj(cnpj)
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def generate_cnpj() -> str:
    """
    Generate a valid random CNPJ (for testing purposes).

    Returns:
        Valid CNPJ string (formatted)
    """
    import random

    # Generate first 12 digits (8 base + 4 branch)
    digits = [random.randint(0, 9) for _ in range(8)]
    digits.extend([0, 0, 0, 1])  # Default branch /0001

    # Ensure not all same digits
    while len(set(digits)) == 1:
        digits = [random.randint(0, 9) for _ in range(8)]
        digits.extend([0, 0, 0, 1])

    # Calculate first check digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(d * w for d, w in zip(digits, weights1, strict=False))
    remainder = total % 11
    digit1 = 0 if remainder < 2 else 11 - remainder
    digits.append(digit1)

    # Calculate second check digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(d * w for d, w in zip(digits, weights2, strict=False))
    remainder = total % 11
    digit2 = 0 if remainder < 2 else 11 - remainder
    digits.append(digit2)

    return format_cnpj("".join(map(str, digits)))


# Alias for backwards compatibility
is_valid_cnpj = validate_cnpj


# =============================================================================
# CEP Functions
# =============================================================================


def clean_cep(cep: str) -> str:
    """Remove all non-digit characters from CEP."""
    if cep is None:
        return ""
    return re.sub(r"\D", "", str(cep))


def validate_cep(cep: str) -> bool:
    """
    Validate Brazilian postal code (CEP).

    Args:
        cep: CEP string (with or without hyphen)

    Returns:
        True if valid format (8 digits), False otherwise

    Example:
        >>> validate_cep("01310-100")
        True
        >>> validate_cep("12345")
        False
    """
    cep = clean_cep(cep)
    return len(cep) == 8 and cep.isdigit()


def format_cep(cep: str) -> str:
    """
    Format CEP as XXXXX-XXX.

    Args:
        cep: CEP string (digits only or formatted)

    Returns:
        Formatted CEP string

    Example:
        >>> format_cep("01310100")
        "01310-100"
    """
    cep = clean_cep(cep)
    if len(cep) != 8:
        return cep
    return f"{cep[:5]}-{cep[5:]}"


# Alias for backwards compatibility
is_valid_cep = validate_cep


# =============================================================================
# UF Functions
# =============================================================================


def validate_uf(uf: str) -> bool:
    """
    Validate Brazilian state code (UF).

    Args:
        uf: Two-letter state code

    Returns:
        True if valid UF, False otherwise

    Example:
        >>> validate_uf("SP")
        True
        >>> validate_uf("XX")
        False
    """
    if uf is None:
        return False
    return uf.upper().strip() in VALID_UFS


def get_uf_name(uf: str) -> str | None:
    """
    Get full state name from UF code.

    Args:
        uf: Two-letter state code

    Returns:
        Full state name or None if invalid

    Example:
        >>> get_uf_name("MG")
        "Minas Gerais"
    """
    return UF_NAMES.get(uf.upper().strip())


def get_uf_code(uf: str) -> int | None:
    """
    Get IBGE code from UF.

    Args:
        uf: Two-letter state code

    Returns:
        IBGE state code or None if invalid

    Example:
        >>> get_uf_code("MG")
        31
    """
    return UF_CODES.get(uf.upper().strip())


# Alias for backwards compatibility
is_valid_uf = validate_uf


# =============================================================================
# Phone Functions
# =============================================================================


def clean_phone(phone: str) -> str:
    """Remove all non-digit characters from phone number."""
    if phone is None:
        return ""
    return re.sub(r"\D", "", str(phone))


def validate_phone(phone: str, allow_landline: bool = True) -> bool:
    """
    Validate Brazilian phone number.

    Args:
        phone: Phone number string
        allow_landline: If True, accepts both mobile and landline numbers

    Returns:
        True if valid format, False otherwise

    Example:
        >>> validate_phone("(11) 99999-9999")
        True
        >>> validate_phone("11999999999")
        True
        >>> validate_phone("999999999")  # No DDD
        False
    """
    phone = clean_phone(phone)

    # Remove country code if present
    if phone.startswith("55") and len(phone) >= 12:
        phone = phone[2:]

    # Must have DDD (2 digits) + number (8-9 digits)
    if len(phone) not in (10, 11):
        return False

    # DDD must be valid (11-99)
    ddd = int(phone[:2])
    if ddd < 11 or ddd > 99:
        return False

    # Mobile numbers start with 9 and have 9 digits
    # Landline numbers start with 2-5 and have 8 digits
    if len(phone) == 11:
        # Mobile: must start with 9
        return phone[2] == "9"
    else:
        # Landline
        if not allow_landline:
            return False
        return phone[2] in "2345"


def format_phone(phone: str, international: bool = False) -> str:
    """
    Format Brazilian phone number.

    Args:
        phone: Phone number string
        international: If True, includes +55 country code

    Returns:
        Formatted phone number

    Example:
        >>> format_phone("11999999999")
        "(11) 99999-9999"
        >>> format_phone("11999999999", international=True)
        "+55 (11) 99999-9999"
    """
    phone = clean_phone(phone)

    # Remove country code if present
    if phone.startswith("55") and len(phone) >= 12:
        phone = phone[2:]

    prefix = "+55 " if international else ""

    if len(phone) == 11:
        # Mobile
        return f"{prefix}({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:
        # Landline
        return f"{prefix}({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    else:
        return phone


# Alias for backwards compatibility
is_valid_phone = validate_phone


# =============================================================================
# PIS/PASEP Functions
# =============================================================================


def clean_pis(pis: str) -> str:
    """Remove all non-digit characters from PIS/PASEP."""
    if pis is None:
        return ""
    return re.sub(r"\D", "", str(pis))


def validate_pis(pis: str) -> bool:
    """
    Validate PIS/PASEP number using module 11 algorithm.

    Args:
        pis: PIS/PASEP string (with or without formatting)

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_pis("123.45678.90-1")
        True  # (if check digit is correct)
    """
    pis = clean_pis(pis)

    # Must have exactly 11 digits
    if len(pis) != 11:
        return False

    # Reject all same digits
    if pis == pis[0] * 11:
        return False

    # Weights for PIS
    weights = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(pis[i]) * weights[i] for i in range(10))
    remainder = total % 11
    check_digit = 0 if remainder < 2 else 11 - remainder

    return int(pis[10]) == check_digit


def format_pis(pis: str) -> str:
    """
    Format PIS/PASEP as XXX.XXXXX.XX-X.

    Args:
        pis: PIS/PASEP string (digits only)

    Returns:
        Formatted PIS/PASEP string
    """
    pis = clean_pis(pis)
    if len(pis) != 11:
        return pis
    return f"{pis[:3]}.{pis[3:8]}.{pis[8:10]}-{pis[10]}"


# Alias for backwards compatibility
is_valid_pis = validate_pis


# =============================================================================
# CNS (Cartão Nacional de Saúde) Functions
# =============================================================================


def clean_cns(cns: str) -> str:
    """Remove all non-digit characters from CNS."""
    if cns is None:
        return ""
    return re.sub(r"\D", "", str(cns))


def validate_cns(cns: str) -> bool:
    """
    Validate CNS (Cartão Nacional de Saúde) number.

    The CNS has 15 digits and uses different algorithms based on the first digit:
    - 1, 2: Definitive CNS (module 11)
    - 7, 8, 9: Provisional CNS (sum must be multiple of 11)

    Args:
        cns: CNS string (with or without spaces)

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_cns("123456789012345")
        True  # (if valid)
    """
    cns = clean_cns(cns)

    # Must have exactly 15 digits
    if len(cns) != 15:
        return False

    first_digit = cns[0]

    # Definitive CNS (starts with 1 or 2)
    if first_digit in "12":
        # Module 11 algorithm
        pis = cns[:11]
        weights = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5]
        total = sum(int(pis[i]) * weights[i] for i in range(11))
        remainder = total % 11
        dv = 11 - remainder if remainder != 0 else 0

        if dv == 10:
            total = sum(int(pis[i]) * weights[i] for i in range(11)) + 2
            remainder = total % 11
            dv = 11 - remainder if remainder != 0 else 0
            result = f"{pis}001{dv}"
        else:
            result = f"{pis}000{dv}"

        return cns == result

    # Provisional CNS (starts with 7, 8, or 9)
    elif first_digit in "789":
        weights = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        total = sum(int(cns[i]) * weights[i] for i in range(15))
        return total % 11 == 0

    return False


def format_cns(cns: str) -> str:
    """
    Format CNS as XXX XXXX XXXX XXXX.

    Args:
        cns: CNS string (digits only)

    Returns:
        Formatted CNS string
    """
    cns = clean_cns(cns)
    if len(cns) != 15:
        return cns
    return f"{cns[:3]} {cns[3:7]} {cns[7:11]} {cns[11:]}"


# Alias for backwards compatibility
is_valid_cns = validate_cns


# =============================================================================
# Utility Functions
# =============================================================================


def identify_document(document: str) -> str | None:
    """
    Identify the type of Brazilian document.

    Args:
        document: Document string (any format)

    Returns:
        Document type ("cpf", "cnpj", "pis", "cns") or None if unrecognized

    Example:
        >>> identify_document("123.456.789-09")
        "cpf"
        >>> identify_document("11.222.333/0001-81")
        "cnpj"
    """
    cleaned = re.sub(r"\D", "", str(document))

    if len(cleaned) == 11:
        if validate_cpf(cleaned):
            return "cpf"
        if validate_pis(cleaned):
            return "pis"
    elif len(cleaned) == 14:
        if validate_cnpj(cleaned):
            return "cnpj"
    elif len(cleaned) == 15:
        if validate_cns(cleaned):
            return "cns"

    return None
