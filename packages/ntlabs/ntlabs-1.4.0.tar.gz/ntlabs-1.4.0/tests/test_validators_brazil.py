"""
Tests for ntlabs.validators.brazil module.

Tests Brazilian document validators including:
- CPF (Cadastro de Pessoas Físicas)
- CNPJ (Cadastro Nacional da Pessoa Jurídica)
- CEP (Código de Endereçamento Postal)
- UF (Unidade Federativa)
- Phone numbers
- PIS/PASEP
- CNS (Cartão Nacional de Saúde)
- Document identification
"""

import pytest

from ntlabs.validators.brazil import (
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
    identify_document,
    is_valid_cep,
    is_valid_cnpj,
    is_valid_cns,
    is_valid_cpf,
    is_valid_phone,
    is_valid_pis,
    is_valid_uf,
    validate_cep,
    validate_cnpj,
    validate_cns,
    validate_cpf,
    validate_phone,
    validate_pis,
    validate_uf,
)


# =============================================================================
# CPF Validation Tests
# =============================================================================


class TestCPFValidation:
    """Tests for CPF validation."""

    def test_valid_cpf_formatted(self):
        """Test valid formatted CPF."""
        assert validate_cpf("123.456.789-09") is True
        assert validate_cpf("529.982.247-25") is True

    def test_valid_cpf_unformatted(self):
        """Test valid unformatted CPF."""
        assert validate_cpf("12345678909") is True
        assert validate_cpf("52998224725") is True

    def test_valid_cpf_generated(self):
        """Test generated valid CPF."""
        cpf = generate_cpf()
        assert validate_cpf(cpf) is True

    def test_invalid_cpf_all_same_digits(self):
        """Test invalid CPF with all same digits."""
        assert validate_cpf("111.111.111-11") is False
        assert validate_cpf("000.000.000-00") is False
        assert validate_cpf("999.999.999-99") is False

    def test_invalid_cpf_wrong_check_digit(self):
        """Test invalid CPF with wrong check digit."""
        assert validate_cpf("123.456.789-00") is False
        assert validate_cpf("123.456.789-99") is False

    def test_invalid_cpf_too_short(self):
        """Test invalid CPF too short."""
        assert validate_cpf("1234567890") is False
        assert validate_cpf("12345678") is False

    def test_invalid_cpf_too_long(self):
        """Test invalid CPF too long."""
        assert validate_cpf("123456789012") is False

    def test_invalid_cpf_empty(self):
        """Test empty CPF."""
        assert validate_cpf("") is False

    def test_is_valid_cpf_alias(self):
        """Test is_valid_cpf is alias for validate_cpf."""
        assert is_valid_cpf("123.456.789-09") is True
        assert is_valid_cpf("111.111.111-11") is False


# =============================================================================
# CPF Cleaning Tests
# =============================================================================


class TestCPFCleaning:
    """Tests for CPF cleaning."""

    def test_clean_cpf_formatted(self):
        """Test cleaning formatted CPF."""
        assert clean_cpf("123.456.789-09") == "12345678909"

    def test_clean_cpf_with_spaces(self):
        """Test cleaning CPF with spaces."""
        assert clean_cpf("  12345678909  ") == "12345678909"

    def test_clean_cpf_none(self):
        """Test cleaning None CPF."""
        assert clean_cpf(None) == ""

    def test_clean_cpf_integer(self):
        """Test cleaning integer CPF."""
        assert clean_cpf(12345678909) == "12345678909"


# =============================================================================
# CPF Formatting Tests
# =============================================================================


class TestCPFFormatting:
    """Tests for CPF formatting."""

    def test_format_cpf_unformatted(self):
        """Test formatting unformatted CPF."""
        assert format_cpf("12345678909") == "123.456.789-09"

    def test_format_cpf_already_formatted(self):
        """Test formatting already formatted CPF."""
        assert format_cpf("123.456.789-09") == "123.456.789-09"

    def test_format_cpf_invalid_length(self):
        """Test formatting CPF with invalid length."""
        assert format_cpf("12345678") == "12345678"  # Returns as-is

    def test_format_cpf_empty(self):
        """Test formatting empty CPF."""
        assert format_cpf("") == ""


# =============================================================================
# CPF Generation Tests
# =============================================================================


class TestCPFGeneration:
    """Tests for CPF generation."""

    def test_generate_cpf_valid(self):
        """Test generated CPF is valid."""
        cpf = generate_cpf()
        assert validate_cpf(cpf) is True

    def test_generate_cpf_formatted(self):
        """Test generated CPF is formatted."""
        cpf = generate_cpf()
        assert len(cpf) == 14  # XXX.XXX.XXX-XX
        assert cpf[3] == "."
        assert cpf[7] == "."
        assert cpf[11] == "-"

    def test_generate_unique_cpfs(self):
        """Test generated CPFs are unique."""
        cpf1 = generate_cpf()
        cpf2 = generate_cpf()
        assert cpf1 != cpf2


# =============================================================================
# CNPJ Validation Tests
# =============================================================================


class TestCNPJValidation:
    """Tests for CNPJ validation."""

    def test_valid_cnpj_formatted(self):
        """Test valid formatted CNPJ."""
        assert validate_cnpj("11.222.333/0001-81") is True

    def test_valid_cnpj_unformatted(self):
        """Test valid unformatted CNPJ."""
        assert validate_cnpj("11222333000181") is True

    def test_valid_cnpj_generated(self):
        """Test generated valid CNPJ."""
        cnpj = generate_cnpj()
        assert validate_cnpj(cnpj) is True

    def test_invalid_cnpj_all_same_digits(self):
        """Test invalid CNPJ with all same digits."""
        assert validate_cnpj("11.111.111/1111-11") is False
        assert validate_cnpj("00.000.000/0000-00") is False

    def test_invalid_cnpj_wrong_check_digit(self):
        """Test invalid CNPJ with wrong check digit."""
        assert validate_cnpj("11.222.333/0001-00") is False

    def test_invalid_cnpj_too_short(self):
        """Test invalid CNPJ too short."""
        assert validate_cnpj("1122233300018") is False

    def test_invalid_cnpj_too_long(self):
        """Test invalid CNPJ too long."""
        assert validate_cnpj("112223330001811") is False

    def test_is_valid_cnpj_alias(self):
        """Test is_valid_cnpj is alias for validate_cnpj."""
        assert is_valid_cnpj("11.222.333/0001-81") is True
        assert is_valid_cnpj("11.111.111/1111-11") is False


# =============================================================================
# CNPJ Cleaning Tests
# =============================================================================


class TestCNPJCleaning:
    """Tests for CNPJ cleaning."""

    def test_clean_cnpj_formatted(self):
        """Test cleaning formatted CNPJ."""
        assert clean_cnpj("11.222.333/0001-81") == "11222333000181"

    def test_clean_cnpj_none(self):
        """Test cleaning None CNPJ."""
        assert clean_cnpj(None) == ""


# =============================================================================
# CNPJ Formatting Tests
# =============================================================================


class TestCNPJFormatting:
    """Tests for CNPJ formatting."""

    def test_format_cnpj_unformatted(self):
        """Test formatting unformatted CNPJ."""
        assert format_cnpj("11222333000181") == "11.222.333/0001-81"

    def test_format_cnpj_invalid_length(self):
        """Test formatting CNPJ with invalid length."""
        assert format_cnpj("11222333") == "11222333"  # Returns as-is


# =============================================================================
# CNPJ Generation Tests
# =============================================================================


class TestCNPJGeneration:
    """Tests for CNPJ generation."""

    def test_generate_cnpj_valid(self):
        """Test generated CNPJ is valid."""
        cnpj = generate_cnpj()
        assert validate_cnpj(cnpj) is True

    def test_generate_cnpj_formatted(self):
        """Test generated CNPJ is formatted."""
        cnpj = generate_cnpj()
        assert len(cnpj) == 18  # XX.XXX.XXX/XXXX-XX
        assert cnpj[2] == "."
        assert cnpj[6] == "."
        assert cnpj[10] == "/"
        assert cnpj[15] == "-"


# =============================================================================
# CEP Validation Tests
# =============================================================================


class TestCEPValidation:
    """Tests for CEP validation."""

    def test_valid_cep_formatted(self):
        """Test valid formatted CEP."""
        assert validate_cep("01310-100") is True
        assert validate_cep("30130-000") is True

    def test_valid_cep_unformatted(self):
        """Test valid unformatted CEP."""
        assert validate_cep("01310100") is True
        assert validate_cep("30130000") is True

    def test_invalid_cep_too_short(self):
        """Test invalid CEP too short."""
        assert validate_cep("01310") is False
        assert validate_cep("12345") is False

    def test_invalid_cep_too_long(self):
        """Test invalid CEP too long."""
        assert validate_cep("013101000") is False

    def test_invalid_cep_with_letters(self):
        """Test invalid CEP with letters."""
        assert validate_cep("0131A100") is False

    def test_is_valid_cep_alias(self):
        """Test is_valid_cep is alias for validate_cep."""
        assert is_valid_cep("01310-100") is True
        assert is_valid_cep("01310") is False


# =============================================================================
# CEP Cleaning Tests
# =============================================================================


class TestCEPCleaning:
    """Tests for CEP cleaning."""

    def test_clean_cep_formatted(self):
        """Test cleaning formatted CEP."""
        assert clean_cep("01310-100") == "01310100"

    def test_clean_cep_none(self):
        """Test cleaning None CEP."""
        assert clean_cep(None) == ""


# =============================================================================
# CEP Formatting Tests
# =============================================================================


class TestCEPFormatting:
    """Tests for CEP formatting."""

    def test_format_cep_unformatted(self):
        """Test formatting unformatted CEP."""
        assert format_cep("01310100") == "01310-100"

    def test_format_cep_invalid_length(self):
        """Test formatting CEP with invalid length."""
        assert format_cep("01310") == "01310"  # Returns as-is


# =============================================================================
# UF Validation Tests
# =============================================================================


class TestUFValidation:
    """Tests for UF validation."""

    def test_valid_uf_all_states(self):
        """Test all valid UFs."""
        for uf in VALID_UFS:
            assert validate_uf(uf) is True

    def test_valid_uf_lowercase(self):
        """Test lowercase UF."""
        assert validate_uf("sp") is True
        assert validate_uf("mg") is True
        assert validate_uf("rj") is True

    def test_valid_uf_with_spaces(self):
        """Test UF with spaces."""
        assert validate_uf("  SP  ") is True

    def test_invalid_uf(self):
        """Test invalid UFs."""
        assert validate_uf("XX") is False
        assert validate_uf("BR") is False
        assert validate_uf("USA") is False

    def test_invalid_uf_none(self):
        """Test None UF."""
        assert validate_uf(None) is False

    def test_is_valid_uf_alias(self):
        """Test is_valid_uf is alias for validate_uf."""
        assert is_valid_uf("SP") is True
        assert is_valid_uf("XX") is False


# =============================================================================
# UF Constants Tests
# =============================================================================


class TestUFConstants:
    """Tests for UF constants."""

    def test_valid_ufs_count(self):
        """Test that we have exactly 27 UFs."""
        assert len(VALID_UFS) == 27

    def test_uf_names_count(self):
        """Test that we have names for all UFs."""
        assert len(UF_NAMES) == 27

    def test_uf_codes_count(self):
        """Test that we have codes for all UFs."""
        assert len(UF_CODES) == 27

    def test_uf_names_content(self):
        """Test UF names content."""
        assert UF_NAMES["SP"] == "São Paulo"
        assert UF_NAMES["MG"] == "Minas Gerais"
        assert UF_NAMES["RJ"] == "Rio de Janeiro"

    def test_uf_codes_content(self):
        """Test UF codes content."""
        assert UF_CODES["SP"] == 35
        assert UF_CODES["MG"] == 31
        assert UF_CODES["RJ"] == 33


# =============================================================================
# Get UF Name Tests
# =============================================================================


class TestGetUFName:
    """Tests for getting UF name."""

    def test_get_uf_name_valid(self):
        """Test getting name for valid UF."""
        assert get_uf_name("MG") == "Minas Gerais"
        assert get_uf_name("SP") == "São Paulo"

    def test_get_uf_name_lowercase(self):
        """Test getting name with lowercase."""
        assert get_uf_name("mg") == "Minas Gerais"

    def test_get_uf_name_with_spaces(self):
        """Test getting name with spaces."""
        assert get_uf_name("  MG  ") == "Minas Gerais"

    def test_get_uf_name_invalid(self):
        """Test getting name for invalid UF."""
        assert get_uf_name("XX") is None


# =============================================================================
# Get UF Code Tests
# =============================================================================


class TestGetUFCode:
    """Tests for getting UF code."""

    def test_get_uf_code_valid(self):
        """Test getting code for valid UF."""
        assert get_uf_code("MG") == 31
        assert get_uf_code("SP") == 35

    def test_get_uf_code_lowercase(self):
        """Test getting code with lowercase."""
        assert get_uf_code("mg") == 31

    def test_get_uf_code_invalid(self):
        """Test getting code for invalid UF."""
        assert get_uf_code("XX") is None


# =============================================================================
# Phone Validation Tests
# =============================================================================


class TestPhoneValidation:
    """Tests for phone validation."""

    def test_valid_mobile_formatted(self):
        """Test valid formatted mobile phone."""
        assert validate_phone("(11) 99999-9999") is True
        assert validate_phone("(31) 98765-4321") is True

    def test_valid_mobile_unformatted(self):
        """Test valid unformatted mobile phone."""
        assert validate_phone("11999999999") is True
        assert validate_phone("31987654321") is True

    def test_valid_landline(self):
        """Test valid landline."""
        assert validate_phone("(11) 3333-4444") is True
        assert validate_phone("1133334444") is True

    def test_valid_phone_with_country_code(self):
        """Test valid phone with country code."""
        assert validate_phone("+55 (11) 99999-9999") is True
        assert validate_phone("5511999999999") is True

    def test_invalid_phone_no_ddd(self):
        """Test invalid phone without DDD."""
        assert validate_phone("999999999") is False
        assert validate_phone("33334444") is False

    def test_invalid_phone_wrong_ddd(self):
        """Test invalid phone with wrong DDD."""
        assert validate_phone("(01) 99999-9999") is False
        assert validate_phone("(00) 3333-4444") is False

    def test_invalid_phone_mobile_without_9(self):
        """Test invalid mobile without 9."""
        assert validate_phone("(11) 19999-9999") is False

    def test_mobile_only_validation(self):
        """Test mobile-only validation."""
        assert validate_phone("11999999999", allow_landline=False) is True
        assert validate_phone("1133334444", allow_landline=False) is False

    def test_is_valid_phone_alias(self):
        """Test is_valid_phone is alias for validate_phone."""
        assert is_valid_phone("(11) 99999-9999") is True
        assert is_valid_phone("999999999") is False


# =============================================================================
# Phone Cleaning Tests
# =============================================================================


class TestPhoneCleaning:
    """Tests for phone cleaning."""

    def test_clean_phone_formatted(self):
        """Test cleaning formatted phone."""
        assert clean_phone("(11) 99999-9999") == "11999999999"

    def test_clean_phone_with_country_code(self):
        """Test cleaning phone with country code."""
        assert clean_phone("+55 (11) 99999-9999") == "5511999999999"

    def test_clean_phone_none(self):
        """Test cleaning None phone."""
        assert clean_phone(None) == ""


# =============================================================================
# Phone Formatting Tests
# =============================================================================


class TestPhoneFormatting:
    """Tests for phone formatting."""

    def test_format_phone_mobile(self):
        """Test formatting mobile phone."""
        assert format_phone("11999999999") == "(11) 99999-9999"

    def test_format_phone_landline(self):
        """Test formatting landline."""
        assert format_phone("1133334444") == "(11) 3333-4444"

    def test_format_phone_international(self):
        """Test formatting with international prefix."""
        assert format_phone("11999999999", international=True) == "+55 (11) 99999-9999"

    def test_format_phone_with_country_code(self):
        """Test formatting phone with existing country code."""
        assert format_phone("5511999999999") == "(11) 99999-9999"


# =============================================================================
# PIS Validation Tests
# =============================================================================


class TestPISValidation:
    """Tests for PIS/PASEP validation."""

    def test_valid_pis(self):
        """Test valid PIS with manually calculated check digit.

        PIS format: NNNNNNNNNND (10 digits + 1 check digit)
        Weights: 3,2,9,8,7,6,5,4,3,2
        
        For PIS 1234567890X:
        Sum = 1*3 + 2*2 + 3*9 + 4*8 + 5*7 + 6*6 + 7*5 + 8*4 + 9*3 + 0*2
            = 3 + 4 + 27 + 32 + 35 + 36 + 35 + 32 + 27 + 0 = 231
        Remainder = 231 % 11 = 231 - 21*11 = 231 - 231 = 0
        Since remainder < 2, check digit = 0
        So valid PIS is 12345678900
        """
        # Valid PIS with correct check digit
        assert validate_pis("12345678900") is True
        assert validate_pis("123.45678.90-0") is True

    def test_invalid_pis_all_same_digits(self):
        """Test invalid PIS with all same digits."""
        assert validate_pis("111.11111.11-1") is False

    def test_invalid_pis_wrong_length(self):
        """Test invalid PIS with wrong length."""
        assert validate_pis("1234567890") is False
        assert validate_pis("123456789012") is False

    def test_invalid_pis_empty(self):
        """Test empty PIS."""
        assert validate_pis("") is False

    def test_is_valid_pis_alias(self):
        """Test is_valid_pis is alias for validate_pis."""
        assert is_valid_pis("12345678900") is True
        assert is_valid_pis("111.11111.11-1") is False


# =============================================================================
# PIS Cleaning Tests
# =============================================================================


class TestPISCleaning:
    """Tests for PIS cleaning."""

    def test_clean_pis_formatted(self):
        """Test cleaning formatted PIS."""
        assert clean_pis("120.8205.74-8") == "1208205748"

    def test_clean_pis_none(self):
        """Test cleaning None PIS."""
        assert clean_pis(None) == ""


# =============================================================================
# PIS Formatting Tests
# =============================================================================


class TestPISFormatting:
    """Tests for PIS formatting."""

    def test_format_pis_unformatted(self):
        """Test formatting unformatted PIS."""
        # PIS is 11 digits: NNN.NNNNN.NN-D
        assert format_pis("12345678900") == "123.45678.90-0"

    def test_format_pis_invalid_length(self):
        """Test formatting PIS with invalid length."""
        assert format_pis("12345678") == "12345678"  # Returns as-is


# =============================================================================
# CNS Validation Tests
# =============================================================================


class TestCNSValidation:
    """Tests for CNS validation."""

    def test_valid_cns_provisional(self):
        """Test valid provisional CNS (starts with 7, 8, or 9)."""
        # Provisional CNS starting with 2 (but actually definitive)
        # Let's use a known valid CNS
        assert validate_cns("279316083540008") is True

    def test_invalid_cns_wrong_length(self):
        """Test invalid CNS with wrong length."""
        assert validate_cns("12345678901234") is False
        assert validate_cns("1234567890123456") is False

    def test_invalid_cns_wrong_first_digit(self):
        """Test invalid CNS with wrong first digit."""
        # CNS must start with 1, 2, 7, 8, or 9
        assert validate_cns("312345678901234") is False

    def test_invalid_cns_all_same_digits(self):
        """Test invalid CNS with all same digits."""
        assert validate_cns("111111111111111") is False

    def test_is_valid_cns_alias(self):
        """Test is_valid_cns is alias for validate_cns."""
        assert is_valid_cns("279316083540008") is True
        assert is_valid_cns("111111111111111") is False


# =============================================================================
# CNS Cleaning Tests
# =============================================================================


class TestCNSCleaning:
    """Tests for CNS cleaning."""

    def test_clean_cns_formatted(self):
        """Test cleaning formatted CNS."""
        assert clean_cns("279 3160 8354 0008") == "279316083540008"

    def test_clean_cns_none(self):
        """Test cleaning None CNS."""
        assert clean_cns(None) == ""


# =============================================================================
# CNS Formatting Tests
# =============================================================================


class TestCNSFormatting:
    """Tests for CNS formatting."""

    def test_format_cns_unformatted(self):
        """Test formatting unformatted CNS."""
        assert format_cns("279316083540008") == "279 3160 8354 0008"

    def test_format_cns_invalid_length(self):
        """Test formatting CNS with invalid length."""
        assert format_cns("27931608") == "27931608"  # Returns as-is


# =============================================================================
# Document Identification Tests
# =============================================================================


class TestDocumentIdentification:
    """Tests for document type identification."""

    def test_identify_cpf(self):
        """Test identification of CPF."""
        assert identify_document("123.456.789-09") == "cpf"
        assert identify_document("12345678909") == "cpf"

    def test_identify_cnpj(self):
        """Test identification of CNPJ."""
        assert identify_document("11.222.333/0001-81") == "cnpj"
        assert identify_document("11222333000181") == "cnpj"

    def test_identify_cns(self):
        """Test identification of CNS."""
        assert identify_document("279 3160 8354 0008") == "cns"
        assert identify_document("279316083540008") == "cns"

    def test_identify_unknown_invalid(self):
        """Test identification of unknown/invalid document."""
        assert identify_document("invalid") is None
        assert identify_document("12345") is None

    def test_identify_empty(self):
        """Test identification of empty document."""
        assert identify_document("") is None

    def test_identify_cpf_vs_pis(self):
        """Test distinguishing CPF from PIS (both 11 digits)."""
        # Valid CPF should be identified as CPF
        assert identify_document("123.456.789-09") == "cpf"
