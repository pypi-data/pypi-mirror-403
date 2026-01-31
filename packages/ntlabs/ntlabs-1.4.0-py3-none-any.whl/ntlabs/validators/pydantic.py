"""
Pydantic field validators for use with Pydantic models.

These validators can be used with Pydantic's field_validator decorator
to validate fields in BaseModel classes.

Example:
    from pydantic import BaseModel, field_validator
    from ntlabs.validators.pydantic import cpf_validator, cnpj_validator

    class UserSchema(BaseModel):
        cpf: str
        cnpj: Optional[str] = None

        _validate_cpf = field_validator('cpf')(cpf_validator)
        _validate_cnpj = field_validator('cnpj')(cnpj_validator)
"""

from typing import Any

from .brazil import (
    clean_cep,
    clean_cnpj,
    clean_cns,
    clean_cpf,
    clean_phone,
    clean_pis,
    validate_cep,
    validate_cnpj,
    validate_cns,
    validate_cpf,
    validate_phone,
    validate_pis,
    validate_uf,
)
from .common import validate_email, validate_url, validate_uuid
from .medical import validate_cid10, validate_crm

# =============================================================================
# Brazilian Document Validators
# =============================================================================


def cpf_validator(value: Any) -> str:
    """
    Pydantic validator for CPF.

    Usage:
        class User(BaseModel):
            cpf: str
            _validate_cpf = field_validator('cpf')(cpf_validator)
    """
    if value is None:
        raise ValueError("CPF is required")

    value = str(value).strip()
    cleaned = clean_cpf(value)

    if not validate_cpf(cleaned):
        raise ValueError("Invalid CPF")

    return cleaned


def cpf_validator_optional(value: Any) -> str | None:
    """
    Pydantic validator for optional CPF.

    Usage:
        class User(BaseModel):
            cpf: Optional[str] = None
            _validate_cpf = field_validator('cpf')(cpf_validator_optional)
    """
    if value is None or value == "":
        return None

    return cpf_validator(value)


def cnpj_validator(value: Any) -> str:
    """
    Pydantic validator for CNPJ.

    Usage:
        class Company(BaseModel):
            cnpj: str
            _validate_cnpj = field_validator('cnpj')(cnpj_validator)
    """
    if value is None:
        raise ValueError("CNPJ is required")

    value = str(value).strip()
    cleaned = clean_cnpj(value)

    if not validate_cnpj(cleaned):
        raise ValueError("Invalid CNPJ")

    return cleaned


def cnpj_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional CNPJ."""
    if value is None or value == "":
        return None

    return cnpj_validator(value)


def cep_validator(value: Any) -> str:
    """
    Pydantic validator for CEP.

    Usage:
        class Address(BaseModel):
            cep: str
            _validate_cep = field_validator('cep')(cep_validator)
    """
    if value is None:
        raise ValueError("CEP is required")

    value = str(value).strip()
    cleaned = clean_cep(value)

    if not validate_cep(cleaned):
        raise ValueError("Invalid CEP")

    return cleaned


def cep_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional CEP."""
    if value is None or value == "":
        return None

    return cep_validator(value)


def uf_validator(value: Any) -> str:
    """
    Pydantic validator for UF (Brazilian state code).

    Usage:
        class Address(BaseModel):
            uf: str
            _validate_uf = field_validator('uf')(uf_validator)
    """
    if value is None:
        raise ValueError("UF is required")

    value = str(value).strip().upper()

    if not validate_uf(value):
        raise ValueError("Invalid UF")

    return value


def uf_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional UF."""
    if value is None or value == "":
        return None

    return uf_validator(value)


def phone_validator(value: Any, allow_landline: bool = True) -> str:
    """
    Pydantic validator for Brazilian phone number.

    Usage:
        class Contact(BaseModel):
            phone: str
            _validate_phone = field_validator('phone')(phone_validator)
    """
    if value is None:
        raise ValueError("Phone is required")

    value = str(value).strip()
    cleaned = clean_phone(value)

    if not validate_phone(cleaned, allow_landline=allow_landline):
        raise ValueError("Invalid phone number")

    return cleaned


def phone_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional phone number."""
    if value is None or value == "":
        return None

    return phone_validator(value)


def mobile_phone_validator(value: Any) -> str:
    """Pydantic validator for mobile phone only (no landlines)."""
    if value is None:
        raise ValueError("Mobile phone is required")

    value = str(value).strip()
    cleaned = clean_phone(value)

    if not validate_phone(cleaned, allow_landline=False):
        raise ValueError("Invalid mobile phone number")

    return cleaned


def pis_validator(value: Any) -> str:
    """
    Pydantic validator for PIS/PASEP.

    Usage:
        class Employee(BaseModel):
            pis: str
            _validate_pis = field_validator('pis')(pis_validator)
    """
    if value is None:
        raise ValueError("PIS is required")

    value = str(value).strip()
    cleaned = clean_pis(value)

    if not validate_pis(cleaned):
        raise ValueError("Invalid PIS/PASEP")

    return cleaned


def pis_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional PIS/PASEP."""
    if value is None or value == "":
        return None

    return pis_validator(value)


def cns_validator(value: Any) -> str:
    """
    Pydantic validator for CNS (Cartão Nacional de Saúde).

    Usage:
        class Patient(BaseModel):
            cns: str
            _validate_cns = field_validator('cns')(cns_validator)
    """
    if value is None:
        raise ValueError("CNS is required")

    value = str(value).strip()
    cleaned = clean_cns(value)

    if not validate_cns(cleaned):
        raise ValueError("Invalid CNS")

    return cleaned


def cns_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional CNS."""
    if value is None or value == "":
        return None

    return cns_validator(value)


# =============================================================================
# Common Validators
# =============================================================================


def email_validator(value: Any, allow_disposable: bool = True) -> str:
    """
    Pydantic validator for email.

    Usage:
        class User(BaseModel):
            email: str
            _validate_email = field_validator('email')(email_validator)
    """
    if value is None:
        raise ValueError("Email is required")

    value = str(value).strip().lower()

    if not validate_email(value, allow_disposable=allow_disposable):
        raise ValueError("Invalid email address")

    return value


def email_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional email."""
    if value is None or value == "":
        return None

    return email_validator(value)


def email_validator_no_disposable(value: Any) -> str:
    """Pydantic validator for email that rejects disposable domains."""
    return email_validator(value, allow_disposable=False)


def url_validator(value: Any, require_https: bool = False) -> str:
    """
    Pydantic validator for URL.

    Usage:
        class Link(BaseModel):
            url: str
            _validate_url = field_validator('url')(url_validator)
    """
    if value is None:
        raise ValueError("URL is required")

    value = str(value).strip()

    if not validate_url(value, require_https=require_https):
        raise ValueError("Invalid URL")

    return value


def url_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional URL."""
    if value is None or value == "":
        return None

    return url_validator(value)


def https_url_validator(value: Any) -> str:
    """Pydantic validator for HTTPS URLs only."""
    return url_validator(value, require_https=True)


def uuid_validator(value: Any, version: int | None = None) -> str:
    """
    Pydantic validator for UUID.

    Usage:
        class Resource(BaseModel):
            id: str
            _validate_id = field_validator('id')(uuid_validator)
    """
    if value is None:
        raise ValueError("UUID is required")

    value = str(value).strip()

    if not validate_uuid(value, version=version):
        raise ValueError("Invalid UUID")

    return value


def uuid_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional UUID."""
    if value is None or value == "":
        return None

    return uuid_validator(value)


def uuid4_validator(value: Any) -> str:
    """Pydantic validator for UUID version 4 only."""
    return uuid_validator(value, version=4)


# =============================================================================
# Medical Validators
# =============================================================================


def cid10_validator(value: Any) -> str:
    """
    Pydantic validator for CID-10 code.

    Usage:
        class Diagnosis(BaseModel):
            cid: str
            _validate_cid = field_validator('cid')(cid10_validator)
    """
    if value is None:
        raise ValueError("CID-10 code is required")

    value = str(value).strip().upper()

    if not validate_cid10(value):
        raise ValueError("Invalid CID-10 code")

    return value


def cid10_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional CID-10 code."""
    if value is None or value == "":
        return None

    return cid10_validator(value)


def crm_validator(value: Any, uf: str | None = None) -> str:
    """
    Pydantic validator for CRM number.

    Usage:
        class Doctor(BaseModel):
            crm: str
            _validate_crm = field_validator('crm')(crm_validator)
    """
    if value is None:
        raise ValueError("CRM is required")

    value = str(value).strip()

    if not validate_crm(value, uf=uf):
        raise ValueError("Invalid CRM number")

    return value


def crm_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional CRM number."""
    if value is None or value == "":
        return None

    return crm_validator(value)


# =============================================================================
# Composite Validators (CPF or CNPJ)
# =============================================================================


def cpf_or_cnpj_validator(value: Any) -> str:
    """
    Pydantic validator that accepts either CPF or CNPJ.

    Usage:
        class Entity(BaseModel):
            document: str
            _validate_doc = field_validator('document')(cpf_or_cnpj_validator)
    """
    if value is None:
        raise ValueError("Document is required")

    value = str(value).strip()

    # Try CPF first
    cleaned_cpf = clean_cpf(value)
    if len(cleaned_cpf) == 11 and validate_cpf(cleaned_cpf):
        return cleaned_cpf

    # Try CNPJ
    cleaned_cnpj = clean_cnpj(value)
    if len(cleaned_cnpj) == 14 and validate_cnpj(cleaned_cnpj):
        return cleaned_cnpj

    raise ValueError("Invalid CPF or CNPJ")


def cpf_or_cnpj_validator_optional(value: Any) -> str | None:
    """Pydantic validator for optional CPF or CNPJ."""
    if value is None or value == "":
        return None

    return cpf_or_cnpj_validator(value)
