"""
NTLabs Validators - Comprehensive validation utilities.

This module provides validation, cleaning, and formatting functions for:
- Brazilian documents (CPF, CNPJ, CEP, UF, PIS, CNS)
- Common data types (email, URL, UUID, IP, dates)
- Medical data (vital signs, CID-10, CRM)
- Government data (IBGE codes, contracts, bidding)
- Pydantic field validators for easy integration

Quick Start:
    # Direct validation
    from ntlabs.validators import validate_cpf, validate_email

    is_valid = validate_cpf("123.456.789-09")
    is_valid = validate_email("user@example.com")

    # Cleaning and formatting
    from ntlabs.validators import clean_cpf, format_cpf

    cleaned = clean_cpf("123.456.789-09")  # "12345678909"
    formatted = format_cpf("12345678909")   # "123.456.789-09"

    # Pydantic integration
    from pydantic import BaseModel, field_validator
    from ntlabs.validators import cpf_validator, cnpj_validator

    class UserSchema(BaseModel):
        cpf: str
        cnpj: str

        _validate_cpf = field_validator('cpf')(cpf_validator)
        _validate_cnpj = field_validator('cnpj')(cnpj_validator)
"""

# =============================================================================
# Brazilian Document Validators
# =============================================================================
from .brazil import (
    UF_CODES,
    UF_NAMES,
    VALID_UFS,
    clean_cep,
    clean_cnpj,
    clean_cns,
    clean_cpf,
    clean_phone,
    clean_pis,
    format_cep,
    format_cnpj,
    format_cns,
    format_cpf,
    format_phone,
    format_pis,
    generate_cnpj,
    generate_cpf,
    get_uf_code,
    get_uf_name,
    # Utility
    identify_document,
    is_valid_cep,
    is_valid_cnpj,
    is_valid_cns,
    is_valid_cpf,
    is_valid_phone,
    is_valid_pis,
    is_valid_uf,
    # CEP
    validate_cep,
    # CNPJ
    validate_cnpj,
    # CNS
    validate_cns,
    # CPF
    validate_cpf,
    # Phone
    validate_phone,
    # PIS
    validate_pis,
    # UF
    validate_uf,
)

# =============================================================================
# Common Validators
# =============================================================================
from .common import (
    DISPOSABLE_DOMAINS,
    calculate_password_strength,
    extract_domain_from_url,
    generate_uuid,
    get_email_domain,
    get_ip_version,
    is_valid_date,
    is_valid_email,
    is_valid_ip,
    is_valid_url,
    is_valid_uuid,
    normalize_email,
    parse_date,
    # Date
    validate_date,
    # Email
    validate_email,
    # IP
    validate_ip,
    # Generic
    validate_length,
    validate_numeric_range,
    # Password
    validate_password,
    # URL
    validate_url,
    # UUID
    validate_uuid,
)

# =============================================================================
# Government Validators
# =============================================================================
from .government import (
    BIDDING_MODALITIES,
    BIDDING_THRESHOLDS,
    check_date_anomaly,
    check_supplier_concentration,
    # Anomaly detection
    check_value_anomaly,
    clean_cnae,
    format_cnae,
    get_bidding_modality_name,
    get_state_from_municipality_code,
    is_valid_cnae,
    is_valid_ibge_code,
    # Bidding
    validate_bidding_modality,
    validate_bidding_value_modality,
    # CNAE
    validate_cnae,
    validate_contract_dates,
    # Contracts
    validate_contract_number,
    validate_contract_value,
    validate_ibge_municipality_code,
    # IBGE
    validate_ibge_state_code,
)

# =============================================================================
# Medical Validators
# =============================================================================
from .medical import (
    CID10_CHAPTERS,
    MEDICATION_UNITS,
    VITAL_SIGN_RANGES,
    VitalSignRange,
    # BMI
    calculate_bmi,
    classify_bmi,
    clean_crm,
    format_crm,
    get_cid10_chapter,
    is_valid_cid10,
    is_valid_crm,
    validate_blood_pressure,
    # CID-10
    validate_cid10,
    # CRM
    validate_crm,
    validate_height,
    # Medications
    validate_medication_dosage,
    validate_medication_frequency,
    validate_temperature,
    # Vital signs
    validate_vital_sign,
    validate_weight,
)

# =============================================================================
# Pydantic Field Validators
# =============================================================================
from .pydantic import (
    cep_validator,
    cep_validator_optional,
    # Medical
    cid10_validator,
    cid10_validator_optional,
    cnpj_validator,
    cnpj_validator_optional,
    cns_validator,
    cns_validator_optional,
    # Composite
    cpf_or_cnpj_validator,
    cpf_or_cnpj_validator_optional,
    # Brazilian documents
    cpf_validator,
    cpf_validator_optional,
    crm_validator,
    crm_validator_optional,
    # Common
    email_validator,
    email_validator_no_disposable,
    email_validator_optional,
    https_url_validator,
    mobile_phone_validator,
    phone_validator,
    phone_validator_optional,
    pis_validator,
    pis_validator_optional,
    uf_validator,
    uf_validator_optional,
    url_validator,
    url_validator_optional,
    uuid4_validator,
    uuid_validator,
    uuid_validator_optional,
)

__all__ = [
    # Brazilian - CPF
    "validate_cpf",
    "clean_cpf",
    "format_cpf",
    "generate_cpf",
    "is_valid_cpf",
    # Brazilian - CNPJ
    "validate_cnpj",
    "clean_cnpj",
    "format_cnpj",
    "generate_cnpj",
    "is_valid_cnpj",
    # Brazilian - CEP
    "validate_cep",
    "clean_cep",
    "format_cep",
    "is_valid_cep",
    # Brazilian - UF
    "validate_uf",
    "is_valid_uf",
    "get_uf_name",
    "get_uf_code",
    "VALID_UFS",
    "UF_NAMES",
    "UF_CODES",
    # Brazilian - Phone
    "validate_phone",
    "clean_phone",
    "format_phone",
    "is_valid_phone",
    # Brazilian - PIS
    "validate_pis",
    "clean_pis",
    "format_pis",
    "is_valid_pis",
    # Brazilian - CNS
    "validate_cns",
    "clean_cns",
    "format_cns",
    "is_valid_cns",
    # Brazilian - Utility
    "identify_document",
    # Common - Email
    "validate_email",
    "normalize_email",
    "get_email_domain",
    "is_valid_email",
    "DISPOSABLE_DOMAINS",
    # Common - URL
    "validate_url",
    "extract_domain_from_url",
    "is_valid_url",
    # Common - UUID
    "validate_uuid",
    "generate_uuid",
    "is_valid_uuid",
    # Common - IP
    "validate_ip",
    "get_ip_version",
    "is_valid_ip",
    # Common - Password
    "validate_password",
    "calculate_password_strength",
    # Common - Date
    "validate_date",
    "parse_date",
    "is_valid_date",
    # Common - Generic
    "validate_length",
    "validate_numeric_range",
    # Medical - Vital signs
    "validate_vital_sign",
    "validate_blood_pressure",
    "validate_temperature",
    "VITAL_SIGN_RANGES",
    "VitalSignRange",
    # Medical - CID-10
    "validate_cid10",
    "get_cid10_chapter",
    "is_valid_cid10",
    "CID10_CHAPTERS",
    # Medical - CRM
    "validate_crm",
    "clean_crm",
    "format_crm",
    "is_valid_crm",
    # Medical - Medications
    "validate_medication_dosage",
    "validate_medication_frequency",
    "MEDICATION_UNITS",
    # Medical - BMI
    "calculate_bmi",
    "classify_bmi",
    "validate_weight",
    "validate_height",
    # Government - IBGE
    "validate_ibge_state_code",
    "validate_ibge_municipality_code",
    "get_state_from_municipality_code",
    "is_valid_ibge_code",
    # Government - Contracts
    "validate_contract_number",
    "validate_contract_value",
    "validate_contract_dates",
    # Government - Bidding
    "validate_bidding_modality",
    "get_bidding_modality_name",
    "validate_bidding_value_modality",
    "BIDDING_MODALITIES",
    "BIDDING_THRESHOLDS",
    # Government - CNAE
    "validate_cnae",
    "clean_cnae",
    "format_cnae",
    "is_valid_cnae",
    # Government - Anomaly
    "check_value_anomaly",
    "check_date_anomaly",
    "check_supplier_concentration",
    # Pydantic - Brazilian
    "cpf_validator",
    "cpf_validator_optional",
    "cnpj_validator",
    "cnpj_validator_optional",
    "cep_validator",
    "cep_validator_optional",
    "uf_validator",
    "uf_validator_optional",
    "phone_validator",
    "phone_validator_optional",
    "mobile_phone_validator",
    "pis_validator",
    "pis_validator_optional",
    "cns_validator",
    "cns_validator_optional",
    # Pydantic - Common
    "email_validator",
    "email_validator_optional",
    "email_validator_no_disposable",
    "url_validator",
    "url_validator_optional",
    "https_url_validator",
    "uuid_validator",
    "uuid_validator_optional",
    "uuid4_validator",
    # Pydantic - Medical
    "cid10_validator",
    "cid10_validator_optional",
    "crm_validator",
    "crm_validator_optional",
    # Pydantic - Composite
    "cpf_or_cnpj_validator",
    "cpf_or_cnpj_validator_optional",
]
