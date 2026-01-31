"""
Tests for ntlabs.validators.government module.

Tests government data validators including:
- IBGE codes (state and municipality)
- Government contracts
- Public bidding (licitações)
- CNAE codes
- Anomaly detection
"""

from datetime import date, timedelta

import pytest

from ntlabs.validators.government import (
    BIDDING_MODALITIES,
    BIDDING_THRESHOLDS,
    check_date_anomaly,
    check_supplier_concentration,
    check_value_anomaly,
    clean_cnae,
    format_cnae,
    get_bidding_modality_name,
    get_state_from_municipality_code,
    is_valid_cnae,
    is_valid_ibge_code,
    validate_bidding_modality,
    validate_bidding_value_modality,
    validate_cnae,
    validate_contract_dates,
    validate_contract_number,
    validate_contract_value,
    validate_ibge_municipality_code,
    validate_ibge_state_code,
)


# =============================================================================
# IBGE State Code Tests
# =============================================================================


class TestIBGEStateCode:
    """Tests for IBGE state code validation."""

    def test_valid_state_code_north(self):
        """Test valid North region state codes."""
        assert validate_ibge_state_code(11) is True  # RO
        assert validate_ibge_state_code(12) is True  # AC
        assert validate_ibge_state_code(13) is True  # AM
        assert validate_ibge_state_code(14) is True  # RR
        assert validate_ibge_state_code(15) is True  # PA
        assert validate_ibge_state_code(16) is True  # AP
        assert validate_ibge_state_code(17) is True  # TO

    def test_valid_state_code_northeast(self):
        """Test valid Northeast region state codes."""
        assert validate_ibge_state_code(21) is True  # MA
        assert validate_ibge_state_code(22) is True  # PI
        assert validate_ibge_state_code(23) is True  # CE
        assert validate_ibge_state_code(24) is True  # RN
        assert validate_ibge_state_code(25) is True  # PB
        assert validate_ibge_state_code(26) is True  # PE
        assert validate_ibge_state_code(27) is True  # AL
        assert validate_ibge_state_code(28) is True  # SE
        assert validate_ibge_state_code(29) is True  # BA

    def test_valid_state_code_southeast(self):
        """Test valid Southeast region state codes."""
        assert validate_ibge_state_code(31) is True  # MG
        assert validate_ibge_state_code(32) is True  # ES
        assert validate_ibge_state_code(33) is True  # RJ
        assert validate_ibge_state_code(35) is True  # SP

    def test_valid_state_code_south(self):
        """Test valid South region state codes."""
        assert validate_ibge_state_code(41) is True  # PR
        assert validate_ibge_state_code(42) is True  # SC
        assert validate_ibge_state_code(43) is True  # RS

    def test_valid_state_code_central_west(self):
        """Test valid Central-West region state codes."""
        assert validate_ibge_state_code(50) is True  # MS
        assert validate_ibge_state_code(51) is True  # MT
        assert validate_ibge_state_code(52) is True  # GO
        assert validate_ibge_state_code(53) is True  # DF

    def test_invalid_state_code(self):
        """Test invalid state codes."""
        assert validate_ibge_state_code(0) is False
        assert validate_ibge_state_code(10) is False
        assert validate_ibge_state_code(20) is False
        assert validate_ibge_state_code(30) is False
        assert validate_ibge_state_code(34) is False
        assert validate_ibge_state_code(99) is False
        assert validate_ibge_state_code(100) is False

    def test_state_code_all_valid_count(self):
        """Test that we have exactly 27 valid state codes."""
        valid_codes = [
            11, 12, 13, 14, 15, 16, 17,  # North
            21, 22, 23, 24, 25, 26, 27, 28, 29,  # Northeast
            31, 32, 33, 35,  # Southeast
            41, 42, 43,  # South
            50, 51, 52, 53,  # Central-West
        ]
        assert len(valid_codes) == 27
        for code in valid_codes:
            assert validate_ibge_state_code(code) is True


# =============================================================================
# IBGE Municipality Code Tests
# =============================================================================


class TestIBGEMunicipalityCode:
    """Tests for IBGE municipality code validation."""

    def test_valid_municipality_code(self):
        """Test valid municipality codes."""
        # Belo Horizonte - MG
        assert validate_ibge_municipality_code(3106200) is True
        # São Paulo - SP
        assert validate_ibge_municipality_code(3550308) is True
        # Rio de Janeiro - RJ
        assert validate_ibge_municipality_code(3304557) is True

    def test_invalid_municipality_code_wrong_length(self):
        """Test invalid municipality codes with wrong length."""
        # Too short
        assert validate_ibge_municipality_code(123456) is False
        # Too long
        assert validate_ibge_municipality_code(12345678) is False

    def test_invalid_municipality_code_invalid_state(self):
        """Test invalid municipality codes with invalid state prefix."""
        # Invalid state code prefix (99)
        assert validate_ibge_municipality_code(9999999) is False

    def test_municipality_code_string_input(self):
        """Test municipality code with string input."""
        # Should convert string to int
        assert validate_ibge_municipality_code("3106200") is True
        assert validate_ibge_municipality_code("3550308") is True

    def test_municipality_code_invalid_string(self):
        """Test municipality code with invalid string input."""
        # Non-numeric string should return False
        assert validate_ibge_municipality_code("invalid") is False
        assert validate_ibge_municipality_code("abc1234") is False

    def test_municipality_code_none(self):
        """Test municipality code with None input."""
        assert validate_ibge_municipality_code(None) is False


# =============================================================================
# State from Municipality Code Tests
# =============================================================================


class TestGetStateFromMunicipalityCode:
    """Tests for extracting state code from municipality code."""

    def test_get_state_from_municipality(self):
        """Test extracting state from valid municipality code."""
        # Belo Horizonte - MG (31)
        assert get_state_from_municipality_code(3106200) == 31
        # São Paulo - SP (35)
        assert get_state_from_municipality_code(3550308) == 35
        # Rio de Janeiro - RJ (33)
        assert get_state_from_municipality_code(3304557) == 33

    def test_get_state_from_invalid_municipality(self):
        """Test extracting state from invalid municipality code."""
        assert get_state_from_municipality_code(9999999) is None
        assert get_state_from_municipality_code(123456) is None
        assert get_state_from_municipality_code(None) is None


# =============================================================================
# Backwards Compatibility Alias Tests
# =============================================================================


class TestBackwardsCompatibility:
    """Tests for backwards compatibility aliases."""

    def test_is_valid_ibge_code_alias(self):
        """Test is_valid_ibge_code is an alias for validate_ibge_municipality_code."""
        # Should work the same as validate_ibge_municipality_code
        assert is_valid_ibge_code(3106200) is True
        assert is_valid_ibge_code(9999999) is False


# =============================================================================
# Contract Number Tests
# =============================================================================


class TestContractNumber:
    """Tests for contract number validation."""

    def test_valid_contract_number_simple(self):
        """Test valid simple contract number format."""
        assert validate_contract_number("123/2024") is True
        assert validate_contract_number("1/2024") is True
        assert validate_contract_number("9999/2024") is True

    def test_valid_contract_number_with_dots(self):
        """Test valid contract number with dots."""
        assert validate_contract_number("01.234/2024") is True
        assert validate_contract_number("12.345/2024") is True

    def test_valid_contract_number_with_prefix(self):
        """Test valid contract number with CT prefix."""
        assert validate_contract_number("CT-1234/2024") is True
        assert validate_contract_number("CT.5678/2024") is True
        assert validate_contract_number("CT12345/2024") is True

    def test_valid_contract_number_full_text(self):
        """Test valid contract number with full text."""
        assert validate_contract_number("CONTRATO Nº 123/2024") is True
        assert validate_contract_number("CONTRATO N° 456/2024") is True
        assert validate_contract_number("CONTRATO N 789/2024") is True
        assert validate_contract_number("CONTRATO Nº123/2024") is True

    def test_valid_contract_number_case_insensitive(self):
        """Test contract number validation is case insensitive."""
        assert validate_contract_number("contrato nº 123/2024") is True
        assert validate_contract_number("ct-1234/2024") is True

    def test_invalid_contract_number(self):
        """Test invalid contract numbers."""
        assert validate_contract_number("invalid") is False
        assert validate_contract_number("123") is False
        assert validate_contract_number("123/24") is False  # Wrong year format
        assert validate_contract_number("/2024") is False
        assert validate_contract_number("abc/def") is False

    def test_contract_number_empty(self):
        """Test empty contract number."""
        assert validate_contract_number("") is False

    def test_contract_number_none(self):
        """Test None contract number."""
        assert validate_contract_number(None) is False

    def test_contract_number_whitespace(self):
        """Test contract number with whitespace."""
        assert validate_contract_number("  123/2024  ") is True
        assert validate_contract_number("  CT-1234/2024  ") is True


# =============================================================================
# Contract Value Tests
# =============================================================================


class TestContractValue:
    """Tests for contract value validation."""

    def test_valid_contract_value(self):
        """Test valid contract value."""
        is_valid, error = validate_contract_value(1000.00)
        assert is_valid is True
        assert error is None

    def test_valid_contract_value_zero(self):
        """Test contract value of zero."""
        is_valid, error = validate_contract_value(0)
        assert is_valid is True
        assert error is None

    def test_valid_contract_value_with_min(self):
        """Test contract value with minimum."""
        is_valid, error = validate_contract_value(1000.00, min_value=500.00)
        assert is_valid is True
        assert error is None

    def test_invalid_contract_value_below_min(self):
        """Test contract value below minimum."""
        is_valid, error = validate_contract_value(100.00, min_value=500.00)
        assert is_valid is False
        assert "at least" in error

    def test_valid_contract_value_with_max(self):
        """Test contract value with maximum."""
        is_valid, error = validate_contract_value(1000.00, max_value=5000.00)
        assert is_valid is True
        assert error is None

    def test_invalid_contract_value_above_max(self):
        """Test contract value above maximum."""
        is_valid, error = validate_contract_value(10000.00, max_value=5000.00)
        assert is_valid is False
        assert "exceeds maximum" in error

    def test_contract_value_suspicious_round(self):
        """Test suspiciously round contract value."""
        # Value >= 10000 and divisible by 10000
        is_valid, error = validate_contract_value(50000.00)
        assert is_valid is True
        assert "warning" in error
        assert "suspiciously round" in error

    def test_contract_value_not_suspicious(self):
        """Test non-suspicious contract value."""
        # Value < 10000
        is_valid, error = validate_contract_value(5000.00)
        assert is_valid is True
        assert error is None

        # Value >= 10000 but not divisible by 10000
        is_valid, error = validate_contract_value(12345.67)
        assert is_valid is True
        assert error is None

    def test_invalid_contract_value_non_numeric(self):
        """Test non-numeric contract value."""
        is_valid, error = validate_contract_value("invalid")
        assert is_valid is False
        assert "numeric" in error

    def test_invalid_contract_value_none(self):
        """Test None contract value."""
        is_valid, error = validate_contract_value(None)
        assert is_valid is False
        assert "numeric" in error


# =============================================================================
# Contract Dates Tests
# =============================================================================


class TestContractDates:
    """Tests for contract dates validation."""

    def test_valid_contract_dates(self):
        """Test valid contract dates."""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        is_valid, error = validate_contract_dates(start, end)
        assert is_valid is True
        assert error is None

    def test_invalid_contract_dates_end_before_start(self):
        """Test end date before start date."""
        start = date(2024, 12, 31)
        end = date(2024, 1, 1)
        is_valid, error = validate_contract_dates(start, end)
        assert is_valid is False
        assert "End date must be after" in error

    def test_invalid_contract_dates_same_day(self):
        """Test end date same as start date."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 1)
        is_valid, error = validate_contract_dates(start, end)
        assert is_valid is False

    def test_invalid_contract_dates_exceeds_duration(self):
        """Test contract duration exceeding maximum."""
        start = date(2024, 1, 1)
        end = date(2029, 1, 1)  # More than 5 years
        is_valid, error = validate_contract_dates(start, end, max_duration_days=1825)
        assert is_valid is False
        assert "exceeds" in error

    def test_valid_contract_dates_with_signature(self):
        """Test valid contract dates with signature date."""
        start = date(2024, 1, 15)
        end = date(2024, 12, 31)
        signature = date(2024, 1, 1)
        is_valid, error = validate_contract_dates(start, end, signature)
        assert is_valid is True
        assert error is None

    def test_invalid_signature_after_start(self):
        """Test signature date after start date."""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        signature = date(2024, 2, 1)
        is_valid, error = validate_contract_dates(start, end, signature)
        assert is_valid is False
        assert "signature date should be before" in error.lower()

    def test_warning_signature_far_in_past(self):
        """Test warning for signature date far in the past."""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        signature = date(2022, 12, 1)  # More than a year before start
        is_valid, error = validate_contract_dates(start, end, signature)
        assert is_valid is True
        assert "warning" in error
        assert "over a year" in error


# =============================================================================
# Bidding Modality Tests
# =============================================================================


class TestBiddingModality:
    """Tests for bidding modality validation."""

    def test_valid_bidding_modality(self):
        """Test valid bidding modalities."""
        assert validate_bidding_modality("CONCORRENCIA") is True
        assert validate_bidding_modality("TOMADA_PRECOS") is True
        assert validate_bidding_modality("CONVITE") is True
        assert validate_bidding_modality("CONCURSO") is True
        assert validate_bidding_modality("LEILAO") is True
        assert validate_bidding_modality("PREGAO_ELETRONICO") is True
        assert validate_bidding_modality("PREGAO_PRESENCIAL") is True
        assert validate_bidding_modality("RDC") is True
        assert validate_bidding_modality("DISPENSA") is True
        assert validate_bidding_modality("INEXIGIBILIDADE") is True

    def test_valid_bidding_modality_lowercase(self):
        """Test lowercase bidding modalities."""
        assert validate_bidding_modality("concorrencia") is True
        assert validate_bidding_modality("pregao_eletronico") is True
        assert validate_bidding_modality("dispensa") is True

    def test_valid_bidding_modality_with_spaces(self):
        """Test bidding modalities with spaces."""
        # Spaces are converted to underscores
        assert validate_bidding_modality("PREGAO ELETRONICO") is True
        assert validate_bidding_modality("TOMADA PRECOS") is True

    def test_valid_bidding_modality_with_hyphens(self):
        """Test bidding modalities with hyphens."""
        # Hyphens are converted to underscores
        assert validate_bidding_modality("PREGAO-ELETRONICO") is True
        assert validate_bidding_modality("TOMADA-PRECOS") is True

    def test_invalid_bidding_modality(self):
        """Test invalid bidding modalities."""
        assert validate_bidding_modality("INVALID") is False
        assert validate_bidding_modality("OTHER") is False
        assert validate_bidding_modality("CONTRACT") is False

    def test_bidding_modality_empty(self):
        """Test empty bidding modality."""
        assert validate_bidding_modality("") is False

    def test_bidding_modality_none(self):
        """Test None bidding modality."""
        assert validate_bidding_modality(None) is False


# =============================================================================
# Get Bidding Modality Name Tests
# =============================================================================


class TestGetBiddingModalityName:
    """Tests for getting bidding modality names."""

    def test_get_modality_name(self):
        """Test getting modality names."""
        assert get_bidding_modality_name("CONCORRENCIA") == "Concorrência"
        assert get_bidding_modality_name("TOMADA_PRECOS") == "Tomada de Preços"
        assert get_bidding_modality_name("PREGAO_ELETRONICO") == "Pregão Eletrônico"
        assert get_bidding_modality_name("DISPENSA") == "Dispensa de Licitação"

    def test_get_modality_name_lowercase(self):
        """Test getting modality names with lowercase input."""
        assert get_bidding_modality_name("concorrencia") == "Concorrência"
        assert get_bidding_modality_name("dispensa") == "Dispensa de Licitação"

    def test_get_modality_name_invalid(self):
        """Test getting modality name for invalid modality."""
        assert get_bidding_modality_name("INVALID") is None

    def test_get_modality_name_empty(self):
        """Test getting modality name for empty input."""
        assert get_bidding_modality_name("") is None

    def test_get_modality_name_none(self):
        """Test getting modality name for None input."""
        assert get_bidding_modality_name(None) is None

    def test_bidding_modalities_constant(self):
        """Test BIDDING_MODALITIES constant contains all modalities."""
        assert len(BIDDING_MODALITIES) == 10
        assert "CONCORRENCIA" in BIDDING_MODALITIES
        assert "PREGAO_ELETRONICO" in BIDDING_MODALITIES
        assert "DISPENSA" in BIDDING_MODALITIES


# =============================================================================
# Bidding Value Modality Tests
# =============================================================================


class TestBiddingValueModality:
    """Tests for bidding value modality validation."""

    def test_dispensa_threshold_obras(self):
        """Test dispensa threshold for obras."""
        # Below threshold - should suggest dispensa
        is_valid, warning = validate_bidding_value_modality(
            50000.00, "CONCORRENCIA", "obras"
        )
        assert is_valid is True
        assert "dispensa" in warning.lower()

    def test_dispensa_threshold_servicos(self):
        """Test dispensa threshold for servicos."""
        # Below threshold - should suggest dispensa
        is_valid, warning = validate_bidding_value_modality(
            25000.00, "CONCORRENCIA", "servicos"
        )
        assert is_valid is True
        assert "dispensa" in warning.lower()

    def test_dispensa_no_warning(self):
        """Test no warning when using dispensa modality."""
        is_valid, warning = validate_bidding_value_modality(
            50000.00, "DISPENSA", "obras"
        )
        assert is_valid is True
        assert warning is None

    def test_convite_exceeds_limit_obras(self):
        """Test convite exceeding limit for obras."""
        is_valid, warning = validate_bidding_value_modality(
            400000.00, "CONVITE", "obras"
        )
        assert is_valid is False
        assert "exceeds limit" in warning

    def test_convite_within_limit_obras(self):
        """Test convite within limit for obras."""
        is_valid, warning = validate_bidding_value_modality(
            300000.00, "CONVITE", "obras"
        )
        assert is_valid is True
        assert warning is None

    def test_convite_exceeds_limit_servicos(self):
        """Test convite exceeding limit for servicos."""
        is_valid, warning = validate_bidding_value_modality(
            200000.00, "CONVITE", "servicos"
        )
        assert is_valid is False
        assert "exceeds limit" in warning

    def test_tomada_precos_exceeds_limit_obras(self):
        """Test tomada de precos exceeding limit for obras."""
        is_valid, warning = validate_bidding_value_modality(
            4000000.00, "TOMADA_PRECOS", "obras"
        )
        assert is_valid is False
        assert "exceeds limit" in warning

    def test_tomada_precos_within_limit_obras(self):
        """Test tomada de precos within limit for obras."""
        is_valid, warning = validate_bidding_value_modality(
            3000000.00, "TOMADA_PRECOS", "obras"
        )
        assert is_valid is True
        assert warning is None

    def test_tomada_precos_exceeds_limit_servicos(self):
        """Test tomada de precos exceeding limit for servicos."""
        is_valid, warning = validate_bidding_value_modality(
            1500000.00, "TOMADA_PRECOS", "servicos"
        )
        assert is_valid is False
        assert "exceeds limit" in warning

    def test_invalid_contract_type_defaults_to_servicos(self):
        """Test invalid contract type defaults to servicos."""
        is_valid, warning = validate_bidding_value_modality(
            25000.00, "CONCORRENCIA", "invalid_type"
        )
        assert is_valid is True
        # Should warn about using dispensa (servicos threshold is 50000)
        assert "dispensa" in warning.lower()

    def test_bidding_thresholds_constant(self):
        """Test BIDDING_THRESHOLDS constant."""
        assert "DISPENSA_OBRAS" in BIDDING_THRESHOLDS
        assert "CONVITE_SERVICOS" in BIDDING_THRESHOLDS
        assert "TOMADA_PRECOS_OBRAS" in BIDDING_THRESHOLDS


# =============================================================================
# CNAE Tests
# =============================================================================


class TestCNAE:
    """Tests for CNAE validation."""

    def test_clean_cnae(self):
        """Test CNAE cleaning."""
        assert clean_cnae("6201-5/00") == "6201500"
        assert clean_cnae("62015/00") == "6201500"
        assert clean_cnae("6201500") == "6201500"
        assert clean_cnae("62.01-5/00") == "6201500"

    def test_clean_cnae_none(self):
        """Test CNAE cleaning with None."""
        assert clean_cnae(None) == ""

    def test_validate_cnae_valid(self):
        """Test valid CNAE validation."""
        assert validate_cnae("6201-5/00") is True
        assert validate_cnae("62015/00") is True
        assert validate_cnae("6201500") is True

    def test_validate_cnae_invalid_length(self):
        """Test invalid CNAE length."""
        assert validate_cnae("123456") is False  # Too short
        assert validate_cnae("12345678") is False  # Too long

    def test_validate_cnae_invalid_format(self):
        """Test invalid CNAE format."""
        assert validate_cnae("invalid") is False
        assert validate_cnae("abc-def") is False

    def test_format_cnae(self):
        """Test CNAE formatting."""
        assert format_cnae("6201500") == "6201-5/00"
        assert format_cnae("6201-5/00") == "6201-5/00"

    def test_format_cnae_invalid_length(self):
        """Test CNAE formatting with invalid length."""
        assert format_cnae("123456") == "123456"  # Returns as-is
        assert format_cnae("12345678") == "12345678"  # Returns as-is

    def test_is_valid_cnae_alias(self):
        """Test is_valid_cnae is alias for validate_cnae."""
        assert is_valid_cnae("6201-5/00") is True
        assert is_valid_cnae("invalid") is False


# =============================================================================
# Anomaly Detection Tests
# =============================================================================


class TestValueAnomaly:
    """Tests for value anomaly detection."""

    def test_no_anomaly(self):
        """Test value within normal range."""
        is_anomalous, description = check_value_anomaly(100, 100, 10, threshold=2.0)
        assert is_anomalous is False
        assert description is None

    def test_anomaly_above_mean(self):
        """Test value significantly above mean."""
        is_anomalous, description = check_value_anomaly(150, 100, 10, threshold=2.0)
        assert is_anomalous is True
        assert "above" in description
        assert "std devs" in description

    def test_anomaly_below_mean(self):
        """Test value significantly below mean."""
        is_anomalous, description = check_value_anomaly(50, 100, 10, threshold=2.0)
        assert is_anomalous is True
        assert "below" in description
        assert "std devs" in description

    def test_no_anomaly_within_threshold(self):
        """Test value within threshold."""
        # 115 is 1.5 std devs above mean (within threshold of 2.0)
        is_anomalous, description = check_value_anomaly(115, 100, 10, threshold=2.0)
        assert is_anomalous is False
        assert description is None

    def test_zero_std_dev_exact_match(self):
        """Test zero standard deviation with exact match."""
        is_anomalous, description = check_value_anomaly(100, 100, 0)
        assert is_anomalous is False
        assert description is None

    def test_zero_std_dev_no_match(self):
        """Test zero standard deviation without exact match."""
        is_anomalous, description = check_value_anomaly(101, 100, 0)
        assert is_anomalous is True
        assert "exact match required" in description


class TestDateAnomaly:
    """Tests for date anomaly detection."""

    def test_no_date_anomaly(self):
        """Test date within tolerance."""
        event_date = date(2024, 1, 15)
        expected_date = date(2024, 1, 10)
        is_anomalous, description = check_date_anomaly(
            event_date, expected_date, tolerance_days=30
        )
        assert is_anomalous is False
        assert description is None

    def test_date_anomaly_after(self):
        """Test date significantly after expected."""
        event_date = date(2024, 3, 1)
        expected_date = date(2024, 1, 1)
        is_anomalous, description = check_date_anomaly(
            event_date, expected_date, tolerance_days=30
        )
        assert is_anomalous is True
        assert "after" in description
        assert "60 days" in description

    def test_date_anomaly_before(self):
        """Test date significantly before expected."""
        event_date = date(2023, 11, 1)
        expected_date = date(2024, 1, 1)
        is_anomalous, description = check_date_anomaly(
            event_date, expected_date, tolerance_days=30
        )
        assert is_anomalous is True
        assert "before" in description
        assert "61 days" in description

    def test_date_anomaly_exact_tolerance(self):
        """Test date exactly at tolerance limit."""
        event_date = date(2024, 1, 31)
        expected_date = date(2024, 1, 1)
        is_anomalous, description = check_date_anomaly(
            event_date, expected_date, tolerance_days=30
        )
        # 30 days difference should NOT be anomalous (<= tolerance)
        assert is_anomalous is False
        assert description is None

    def test_date_anomaly_one_day_over(self):
        """Test date one day over tolerance."""
        event_date = date(2024, 2, 1)
        expected_date = date(2024, 1, 1)
        is_anomalous, description = check_date_anomaly(
            event_date, expected_date, tolerance_days=30
        )
        # 31 days difference should be anomalous (> tolerance)
        assert is_anomalous is True
        assert "31 days" in description


class TestSupplierConcentration:
    """Tests for supplier concentration check."""

    def test_no_concentration(self):
        """Test supplier share below threshold."""
        is_suspicious, description = check_supplier_concentration(0.3, threshold=0.5)
        assert is_suspicious is False
        assert description is None

    def test_concentration_above_threshold(self):
        """Test supplier share above threshold."""
        is_suspicious, description = check_supplier_concentration(0.75, threshold=0.5)
        assert is_suspicious is True
        assert "75.0%" in description

    def test_concentration_at_threshold(self):
        """Test supplier share exactly at threshold."""
        is_suspicious, description = check_supplier_concentration(0.5, threshold=0.5)
        # At threshold should NOT be suspicious (needs to be > threshold)
        assert is_suspicious is False
        assert description is None

    def test_concentration_custom_threshold(self):
        """Test supplier concentration with custom threshold."""
        is_suspicious, description = check_supplier_concentration(0.4, threshold=0.3)
        assert is_suspicious is True
        assert "40.0%" in description
