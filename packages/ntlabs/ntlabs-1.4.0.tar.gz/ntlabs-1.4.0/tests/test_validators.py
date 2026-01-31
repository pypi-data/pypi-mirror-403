"""
Tests for ntlabs.validators module.

Tests Brazilian document validation (CPF, CNPJ, CEP, etc.),
common validators (email, URL, UUID), and medical validators.
"""

from ntlabs.validators import (
    VALID_UFS,
    calculate_bmi,
    calculate_password_strength,
    classify_bmi,
    clean_cep,
    clean_cnpj,
    clean_cpf,
    extract_domain_from_url,
    format_cep,
    format_cnae,
    format_cnpj,
    format_cpf,
    format_crm,
    format_phone,
    generate_cnpj,
    generate_cpf,
    generate_uuid,
    get_cid10_chapter,
    get_email_domain,
    get_uf_code,
    get_uf_name,
    identify_document,
    normalize_email,
    validate_blood_pressure,
    validate_cep,
    validate_cid10,
    validate_cnae,
    validate_cnpj,
    validate_contract_number,
    # Brazilian
    validate_cpf,
    validate_crm,
    # Common
    validate_email,
    validate_ibge_municipality_code,
    # Government
    validate_ibge_state_code,
    validate_medication_dosage,
    validate_medication_frequency,
    validate_password,
    validate_phone,
    validate_temperature,
    validate_uf,
    validate_url,
    validate_uuid,
    validate_vital_sign,
)

# =============================================================================
# CPF Tests
# =============================================================================


class TestCPFValidation:
    """Tests for CPF validation."""

    def test_valid_cpf_formatted(self):
        """Test valid CPF with formatting."""
        assert validate_cpf("123.456.789-09") is True

    def test_valid_cpf_unformatted(self):
        """Test valid CPF without formatting."""
        assert validate_cpf("12345678909") is True

    def test_invalid_cpf_wrong_check_digits(self):
        """Test CPF with wrong check digits."""
        assert validate_cpf("123.456.789-00") is False

    def test_invalid_cpf_all_same_digits(self):
        """Test CPF with all same digits."""
        assert validate_cpf("111.111.111-11") is False
        assert validate_cpf("000.000.000-00") is False

    def test_invalid_cpf_too_short(self):
        """Test CPF with wrong length."""
        assert validate_cpf("12345") is False
        assert validate_cpf("") is False

    def test_clean_cpf(self):
        """Test CPF cleaning."""
        assert clean_cpf("123.456.789-09") == "12345678909"
        assert clean_cpf("  12345678909  ") == "12345678909"
        assert clean_cpf(None) == ""

    def test_format_cpf(self):
        """Test CPF formatting."""
        assert format_cpf("12345678909") == "123.456.789-09"
        assert format_cpf("12345") == "12345"  # Invalid length unchanged

    def test_generate_cpf(self):
        """Test CPF generation."""
        cpf = generate_cpf()
        assert validate_cpf(cpf) is True


# =============================================================================
# CNPJ Tests
# =============================================================================


class TestCNPJValidation:
    """Tests for CNPJ validation."""

    def test_valid_cnpj_formatted(self):
        """Test valid CNPJ with formatting."""
        assert validate_cnpj("11.222.333/0001-81") is True

    def test_valid_cnpj_unformatted(self):
        """Test valid CNPJ without formatting."""
        assert validate_cnpj("11222333000181") is True

    def test_invalid_cnpj_wrong_check_digits(self):
        """Test CNPJ with wrong check digits."""
        assert validate_cnpj("11.222.333/0001-00") is False

    def test_invalid_cnpj_all_same_digits(self):
        """Test CNPJ with all same digits."""
        assert validate_cnpj("11.111.111/1111-11") is False

    def test_clean_cnpj(self):
        """Test CNPJ cleaning."""
        assert clean_cnpj("11.222.333/0001-81") == "11222333000181"

    def test_format_cnpj(self):
        """Test CNPJ formatting."""
        assert format_cnpj("11222333000181") == "11.222.333/0001-81"

    def test_generate_cnpj(self):
        """Test CNPJ generation."""
        cnpj = generate_cnpj()
        assert validate_cnpj(cnpj) is True


# =============================================================================
# CEP Tests
# =============================================================================


class TestCEPValidation:
    """Tests for CEP validation."""

    def test_valid_cep_formatted(self):
        """Test valid CEP with hyphen."""
        assert validate_cep("01310-100") is True

    def test_valid_cep_unformatted(self):
        """Test valid CEP without hyphen."""
        assert validate_cep("01310100") is True

    def test_invalid_cep_wrong_length(self):
        """Test CEP with wrong length."""
        assert validate_cep("12345") is False
        assert validate_cep("123456789") is False

    def test_invalid_cep_with_letters(self):
        """Test CEP with letters."""
        assert validate_cep("0131A100") is False

    def test_clean_cep(self):
        """Test CEP cleaning."""
        assert clean_cep("01310-100") == "01310100"

    def test_format_cep(self):
        """Test CEP formatting."""
        assert format_cep("01310100") == "01310-100"


# =============================================================================
# UF Tests
# =============================================================================


class TestUFValidation:
    """Tests for UF validation."""

    def test_valid_uf(self):
        """Test valid UF codes."""
        assert validate_uf("SP") is True
        assert validate_uf("MG") is True
        assert validate_uf("RJ") is True

    def test_valid_uf_lowercase(self):
        """Test UF with lowercase."""
        assert validate_uf("sp") is True

    def test_invalid_uf(self):
        """Test invalid UF codes."""
        assert validate_uf("XX") is False
        assert validate_uf("BR") is False

    def test_get_uf_name(self):
        """Test UF name lookup."""
        assert get_uf_name("MG") == "Minas Gerais"
        assert get_uf_name("SP") == "São Paulo"
        assert get_uf_name("XX") is None

    def test_get_uf_code(self):
        """Test IBGE UF code lookup."""
        assert get_uf_code("MG") == 31
        assert get_uf_code("SP") == 35

    def test_valid_ufs_count(self):
        """Test we have all 27 UFs."""
        assert len(VALID_UFS) == 27


# =============================================================================
# Phone Tests
# =============================================================================


class TestPhoneValidation:
    """Tests for phone validation."""

    def test_valid_mobile_formatted(self):
        """Test valid mobile phone formatted."""
        assert validate_phone("(11) 99999-9999") is True

    def test_valid_mobile_unformatted(self):
        """Test valid mobile phone unformatted."""
        assert validate_phone("11999999999") is True

    def test_valid_landline(self):
        """Test valid landline."""
        assert validate_phone("1133334444") is True

    def test_valid_phone_with_country_code(self):
        """Test phone with country code."""
        assert validate_phone("+55 11 99999-9999") is True
        assert validate_phone("5511999999999") is True

    def test_invalid_phone_no_ddd(self):
        """Test phone without DDD."""
        assert validate_phone("999999999") is False

    def test_mobile_only_validation(self):
        """Test mobile-only validation."""
        assert validate_phone("11999999999", allow_landline=False) is True
        assert validate_phone("1133334444", allow_landline=False) is False

    def test_format_phone(self):
        """Test phone formatting."""
        assert format_phone("11999999999") == "(11) 99999-9999"
        assert format_phone("1133334444") == "(11) 3333-4444"
        assert format_phone("11999999999", international=True) == "+55 (11) 99999-9999"


# =============================================================================
# Email Tests
# =============================================================================


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email addresses."""
        assert validate_email("user@example.com") is True
        assert validate_email("user.name@example.com") is True
        assert validate_email("user+tag@example.co.uk") is True

    def test_invalid_email(self):
        """Test invalid email addresses."""
        assert validate_email("invalid") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("") is False

    def test_disposable_email_rejection(self):
        """Test disposable email rejection."""
        assert validate_email("user@mailinator.com", allow_disposable=True) is True
        assert validate_email("user@mailinator.com", allow_disposable=False) is False

    def test_normalize_email(self):
        """Test email normalization."""
        assert normalize_email("  USER@Example.COM  ") == "user@example.com"

    def test_get_email_domain(self):
        """Test domain extraction."""
        assert get_email_domain("user@example.com") == "example.com"


# =============================================================================
# URL Tests
# =============================================================================


class TestURLValidation:
    """Tests for URL validation."""

    def test_valid_urls(self):
        """Test valid URLs."""
        assert validate_url("https://example.com") is True
        assert validate_url("http://example.com/path") is True
        assert validate_url("https://example.com:8080/path?query=1") is True

    def test_invalid_urls(self):
        """Test invalid URLs."""
        assert validate_url("not-a-url") is False
        assert validate_url("ftp://example.com") is False  # Not http(s)

    def test_require_https(self):
        """Test HTTPS requirement."""
        assert validate_url("https://example.com", require_https=True) is True
        assert validate_url("http://example.com", require_https=True) is False

    def test_extract_domain(self):
        """Test domain extraction from URL."""
        assert (
            extract_domain_from_url("https://www.example.com/path") == "www.example.com"
        )


# =============================================================================
# UUID Tests
# =============================================================================


class TestUUIDValidation:
    """Tests for UUID validation."""

    def test_valid_uuid(self):
        """Test valid UUID."""
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_invalid_uuid(self):
        """Test invalid UUID."""
        assert validate_uuid("not-a-uuid") is False
        assert validate_uuid("") is False

    def test_uuid_version(self):
        """Test UUID version checking."""
        uuid4 = generate_uuid(version=4)
        assert validate_uuid(uuid4, version=4) is True


# =============================================================================
# Password Tests
# =============================================================================


class TestPasswordValidation:
    """Tests for password validation."""

    def test_strong_password(self):
        """Test strong password validation."""
        is_valid, errors = validate_password("SecurePass123!")
        assert is_valid is True
        assert len(errors) == 0

    def test_weak_password(self):
        """Test weak password detection."""
        is_valid, errors = validate_password("weak")
        assert is_valid is False
        assert len(errors) > 0

    def test_password_strength_calculation(self):
        """Test password strength score."""
        assert calculate_password_strength("") == 0
        assert calculate_password_strength("a") < 50
        assert calculate_password_strength("SecurePassword123!") > 50


# =============================================================================
# Medical Validators Tests
# =============================================================================


class TestMedicalValidators:
    """Tests for medical validators."""

    def test_vital_sign_normal(self):
        """Test normal vital sign."""
        is_valid, status = validate_vital_sign(75, "heart_rate")
        assert is_valid is True
        assert status == "normal"

    def test_vital_sign_high(self):
        """Test high vital sign."""
        is_valid, status = validate_vital_sign(120, "heart_rate")
        assert is_valid is True
        assert status == "high"

    def test_blood_pressure_normal(self):
        """Test normal blood pressure."""
        is_valid, classification = validate_blood_pressure(115, 75)
        assert is_valid is True
        assert classification == "normal"

    def test_blood_pressure_hypertension(self):
        """Test hypertensive blood pressure."""
        is_valid, classification = validate_blood_pressure(145, 95)
        assert is_valid is True
        assert classification == "hypertension_stage_2"

    def test_temperature_normal(self):
        """Test normal temperature."""
        is_valid, classification = validate_temperature(36.5)
        assert is_valid is True
        assert classification == "normal"

    def test_temperature_fever(self):
        """Test fever detection."""
        is_valid, classification = validate_temperature(38.5)
        assert is_valid is True
        assert classification == "moderate_fever"

    def test_valid_cid10(self):
        """Test valid CID-10 codes."""
        assert validate_cid10("J18") is True
        assert validate_cid10("J18.0") is True
        assert validate_cid10("A01.1") is True

    def test_invalid_cid10(self):
        """Test invalid CID-10 codes."""
        assert validate_cid10("invalid") is False
        assert validate_cid10("123") is False

    def test_cid10_chapter(self):
        """Test CID-10 chapter lookup."""
        chapter = get_cid10_chapter("J18")
        assert "Respiratory" in chapter

    def test_valid_crm(self):
        """Test valid CRM numbers."""
        assert validate_crm("12345-MG") is True
        assert validate_crm("123456SP") is True
        assert validate_crm("123456", uf="SP") is True

    def test_format_crm(self):
        """Test CRM formatting."""
        assert format_crm("12345MG") == "CRM/MG 12345"

    def test_medication_dosage(self):
        """Test medication dosage validation."""
        is_valid, parsed = validate_medication_dosage("500mg")
        assert is_valid is True
        assert parsed["value"] == 500
        assert parsed["unit"] == "mg"

    def test_medication_frequency(self):
        """Test medication frequency validation."""
        is_valid, parsed = validate_medication_frequency("8/8h")
        assert is_valid is True
        assert parsed["times_per_day"] == 3

    def test_bmi_calculation(self):
        """Test BMI calculation."""
        bmi = calculate_bmi(70, 175)
        assert 22 < bmi < 24

    def test_bmi_classification(self):
        """Test BMI classification."""
        assert classify_bmi(22) == "normal"
        assert classify_bmi(28) == "overweight"
        assert classify_bmi(32) == "obese_class_1"


# =============================================================================
# Government Validators Tests
# =============================================================================


class TestGovernmentValidators:
    """Tests for government validators."""

    def test_ibge_state_code(self):
        """Test IBGE state code validation."""
        assert validate_ibge_state_code(31) is True  # MG
        assert validate_ibge_state_code(35) is True  # SP
        assert validate_ibge_state_code(99) is False

    def test_ibge_municipality_code(self):
        """Test IBGE municipality code validation."""
        assert validate_ibge_municipality_code(3106200) is True  # Belo Horizonte
        # Note: validation only checks format (7 digits, valid state code prefix)
        # 1234567 has valid format - use invalid prefix like 9999999
        assert validate_ibge_municipality_code(9999999) is False  # Invalid state code

    def test_contract_number(self):
        """Test contract number validation."""
        assert validate_contract_number("123/2024") is True
        assert validate_contract_number("CT-4567/2024") is True

    def test_cnae_validation(self):
        """Test CNAE validation."""
        assert validate_cnae("6201-5/00") is True
        assert validate_cnae("6201500") is True
        assert validate_cnae("invalid") is False

    def test_cnae_formatting(self):
        """Test CNAE formatting."""
        assert format_cnae("6201500") == "6201-5/00"


# =============================================================================
# Document Identification Tests
# =============================================================================


class TestDocumentIdentification:
    """Tests for document type identification."""

    def test_identify_cpf(self):
        """Test CPF identification."""
        assert identify_document("123.456.789-09") == "cpf"

    def test_identify_cnpj(self):
        """Test CNPJ identification."""
        assert identify_document("11.222.333/0001-81") == "cnpj"

    def test_identify_unknown(self):
        """Test unknown document."""
        assert identify_document("invalid") is None
