"""
Tests for ntlabs.validators.medical module.

Tests medical data validators including:
- Vital signs (heart rate, blood pressure, temperature, etc.)
- CID-10 codes (ICD-10)
- CRM numbers
- Medication dosages and frequencies
- BMI calculation and classification
"""

import pytest

from ntlabs.validators.medical import (
    CID10_CHAPTERS,
    MEDICATION_UNITS,
    VITAL_SIGN_RANGES,
    VitalSignRange,
    calculate_bmi,
    classify_bmi,
    clean_crm,
    format_crm,
    get_cid10_chapter,
    is_valid_cid10,
    is_valid_crm,
    validate_blood_pressure,
    validate_cid10,
    validate_crm,
    validate_height,
    validate_medication_dosage,
    validate_medication_frequency,
    validate_temperature,
    validate_vital_sign,
    validate_weight,
)


# =============================================================================
# Vital Sign Range Tests
# =============================================================================


class TestVitalSignRanges:
    """Tests for vital sign range definitions."""

    def test_vital_sign_ranges_exist(self):
        """Test that all expected vital sign ranges exist."""
        assert "heart_rate" in VITAL_SIGN_RANGES
        assert "systolic_bp" in VITAL_SIGN_RANGES
        assert "diastolic_bp" in VITAL_SIGN_RANGES
        assert "temperature" in VITAL_SIGN_RANGES
        assert "respiratory_rate" in VITAL_SIGN_RANGES
        assert "oxygen_saturation" in VITAL_SIGN_RANGES
        assert "glucose" in VITAL_SIGN_RANGES

    def test_vital_sign_range_structure(self):
        """Test vital sign range has correct structure."""
        hr_range = VITAL_SIGN_RANGES["heart_rate"]
        assert hr_range.name == "Heart Rate"
        assert hr_range.unit == "bpm"
        assert hr_range.normal_min == 60
        assert hr_range.normal_max == 100
        assert hr_range.critical_min == 40
        assert hr_range.critical_max == 150

    def test_vital_sign_range_dataclass(self):
        """Test VitalSignRange dataclass."""
        vsr = VitalSignRange(
            name="Test",
            unit="test",
            normal_min=50,
            normal_max=100,
            critical_min=30,
            critical_max=120,
        )
        assert vsr.name == "Test"
        assert vsr.absolute_min == 0  # Default value
        assert vsr.absolute_max == float("inf")  # Default value


# =============================================================================
# Vital Sign Validation Tests
# =============================================================================


class TestVitalSignValidation:
    """Tests for vital sign validation."""

    def test_heart_rate_normal(self):
        """Test normal heart rate."""
        is_valid, status = validate_vital_sign(75, "heart_rate")
        assert is_valid is True
        assert status == "normal"

    def test_heart_rate_low(self):
        """Test low heart rate."""
        is_valid, status = validate_vital_sign(50, "heart_rate")
        assert is_valid is True
        assert status == "low"

    def test_heart_rate_high(self):
        """Test high heart rate."""
        is_valid, status = validate_vital_sign(110, "heart_rate")
        assert is_valid is True
        assert status == "high"

    def test_heart_rate_critical_low(self):
        """Test critically low heart rate."""
        is_valid, status = validate_vital_sign(35, "heart_rate")
        assert is_valid is True
        assert status == "critical_low"

    def test_heart_rate_critical_high(self):
        """Test critically high heart rate."""
        is_valid, status = validate_vital_sign(160, "heart_rate")
        assert is_valid is True
        assert status == "critical_high"

    def test_heart_rate_invalid(self):
        """Test invalid heart rate."""
        is_valid, status = validate_vital_sign(-10, "heart_rate")
        assert is_valid is False
        assert status == "invalid"

    def test_heart_rate_absolute_max(self):
        """Test heart rate above absolute maximum."""
        is_valid, status = validate_vital_sign(350, "heart_rate")
        assert is_valid is False
        assert status == "invalid"

    def test_unknown_vital_sign(self):
        """Test unknown vital sign type."""
        is_valid, status = validate_vital_sign(100, "unknown_type")
        assert is_valid is False
        assert "Unknown" in status

    def test_vital_sign_no_critical_check(self):
        """Test vital sign without critical check."""
        # Should not report critical even if value is in critical range
        is_valid, status = validate_vital_sign(35, "heart_rate", check_critical=False)
        assert is_valid is True
        # Without critical check, should be "low" not "critical_low"
        assert status == "low"

    def test_systolic_bp_normal(self):
        """Test normal systolic BP."""
        is_valid, status = validate_vital_sign(110, "systolic_bp")
        assert is_valid is True
        assert status == "normal"

    def test_diastolic_bp_high(self):
        """Test high diastolic BP."""
        is_valid, status = validate_vital_sign(90, "diastolic_bp")
        assert is_valid is True
        assert status == "high"

    def test_temperature_normal(self):
        """Test normal temperature."""
        is_valid, status = validate_vital_sign(36.8, "temperature")
        assert is_valid is True
        assert status == "normal"

    def test_temperature_fever(self):
        """Test fever temperature."""
        is_valid, status = validate_vital_sign(38.5, "temperature")
        assert is_valid is True
        assert status == "high"

    def test_respiratory_rate_normal(self):
        """Test normal respiratory rate."""
        is_valid, status = validate_vital_sign(16, "respiratory_rate")
        assert is_valid is True
        assert status == "normal"

    def test_oxygen_saturation_normal(self):
        """Test normal oxygen saturation."""
        is_valid, status = validate_vital_sign(98, "oxygen_saturation")
        assert is_valid is True
        assert status == "normal"

    def test_oxygen_saturation_critical_low(self):
        """Test critically low oxygen saturation."""
        is_valid, status = validate_vital_sign(85, "oxygen_saturation")
        assert is_valid is True
        assert status == "critical_low"

    def test_glucose_normal(self):
        """Test normal glucose level."""
        is_valid, status = validate_vital_sign(85, "glucose")
        assert is_valid is True
        assert status == "normal"


# =============================================================================
# Blood Pressure Tests
# =============================================================================


class TestBloodPressure:
    """Tests for blood pressure validation."""

    def test_bp_normal(self):
        """Test normal blood pressure."""
        is_valid, classification = validate_blood_pressure(115, 75)
        assert is_valid is True
        assert classification == "normal"

    def test_bp_optimal(self):
        """Test optimal blood pressure."""
        is_valid, classification = validate_blood_pressure(110, 70)
        assert is_valid is True
        assert classification == "normal"

    def test_bp_elevated(self):
        """Test elevated blood pressure."""
        is_valid, classification = validate_blood_pressure(125, 78)
        assert is_valid is True
        assert classification == "elevated"

    def test_bp_hypertension_stage_1(self):
        """Test hypertension stage 1."""
        is_valid, classification = validate_blood_pressure(135, 85)
        assert is_valid is True
        assert classification == "hypertension_stage_1"

    def test_bp_hypertension_stage_2(self):
        """Test hypertension stage 2."""
        is_valid, classification = validate_blood_pressure(150, 95)
        assert is_valid is True
        assert classification == "hypertension_stage_2"

    def test_bp_hypertensive_crisis(self):
        """Test hypertensive crisis."""
        is_valid, classification = validate_blood_pressure(190, 120)
        assert is_valid is True
        assert classification == "hypertensive_crisis"

    def test_bp_hypotension(self):
        """Test hypotension."""
        is_valid, classification = validate_blood_pressure(85, 55)
        assert is_valid is True
        assert classification == "hypotension"

    def test_bp_borderline_hypotension(self):
        """Test borderline hypotension."""
        is_valid, classification = validate_blood_pressure(89, 59)
        assert is_valid is True
        assert classification == "hypotension"

    def test_bp_invalid_diastolic_higher(self):
        """Test invalid when diastolic >= systolic."""
        is_valid, classification = validate_blood_pressure(80, 80)
        assert is_valid is False
        assert classification == "invalid"

        is_valid, classification = validate_blood_pressure(80, 90)
        assert is_valid is False
        assert classification == "invalid"

    def test_bp_invalid_negative(self):
        """Test invalid negative values."""
        is_valid, classification = validate_blood_pressure(-10, 80)
        assert is_valid is False
        assert classification == "invalid"

        is_valid, classification = validate_blood_pressure(120, -10)
        assert is_valid is False
        assert classification == "invalid"

    def test_bp_invalid_extreme(self):
        """Test invalid extreme values."""
        is_valid, classification = validate_blood_pressure(350, 80)
        assert is_valid is False
        assert classification == "invalid"

        is_valid, classification = validate_blood_pressure(120, 250)
        assert is_valid is False
        assert classification == "invalid"


# =============================================================================
# Temperature Tests
# =============================================================================


class TestTemperature:
    """Tests for temperature validation."""

    def test_temperature_celsius_normal(self):
        """Test normal temperature in Celsius."""
        is_valid, classification = validate_temperature(36.5, "celsius")
        assert is_valid is True
        assert classification == "normal"

    def test_temperature_celsius_low(self):
        """Test low temperature in Celsius."""
        is_valid, classification = validate_temperature(35.5, "celsius")
        assert is_valid is True
        assert classification == "low"

    def test_temperature_hypothermia(self):
        """Test hypothermia temperature."""
        is_valid, classification = validate_temperature(34.0, "celsius")
        assert is_valid is True
        assert classification == "hypothermia"

    def test_temperature_low_fever(self):
        """Test low fever temperature."""
        is_valid, classification = validate_temperature(37.8, "celsius")
        assert is_valid is True
        assert classification == "low_fever"

    def test_temperature_moderate_fever(self):
        """Test moderate fever temperature."""
        is_valid, classification = validate_temperature(38.5, "celsius")
        assert is_valid is True
        assert classification == "moderate_fever"

    def test_temperature_high_fever(self):
        """Test high fever temperature."""
        is_valid, classification = validate_temperature(40.0, "celsius")
        assert is_valid is True
        assert classification == "high_fever"

    def test_temperature_hyperpyrexia(self):
        """Test hyperpyrexia temperature."""
        is_valid, classification = validate_temperature(41.5, "celsius")
        assert is_valid is True
        assert classification == "hyperpyrexia"

    def test_temperature_fahrenheit(self):
        """Test temperature conversion from Fahrenheit."""
        is_valid, classification = validate_temperature(98.6, "fahrenheit")
        assert is_valid is True
        assert classification == "normal"

    def test_temperature_fahrenheit_fever(self):
        """Test fever temperature in Fahrenheit.
        
        101.3°F = 38.5°C which is moderate fever (38.0-39.0)
        100.4°F = 38.0°C which is the boundary of low fever
        """
        is_valid, classification = validate_temperature(100.4, "fahrenheit")
        assert is_valid is True
        assert classification == "low_fever"

    def test_temperature_fahrenheit_abbr(self):
        """Test temperature with 'f' abbreviation."""
        is_valid, classification = validate_temperature(98.6, "f")
        assert is_valid is True
        assert classification == "normal"

    def test_temperature_invalid_extreme_low(self):
        """Test invalid extreme low temperature."""
        is_valid, classification = validate_temperature(20, "celsius")
        assert is_valid is False
        assert classification == "invalid"

    def test_temperature_invalid_extreme_high(self):
        """Test invalid extreme high temperature."""
        is_valid, classification = validate_temperature(50, "celsius")
        assert is_valid is False
        assert classification == "invalid"


# =============================================================================
# CID-10 Validation Tests
# =============================================================================


class TestCID10Validation:
    """Tests for CID-10 code validation."""

    def test_valid_cid10_simple(self):
        """Test valid simple CID-10 codes."""
        assert validate_cid10("J18") is True
        assert validate_cid10("A01") is True
        assert validate_cid10("M54") is True

    def test_valid_cid10_with_decimal(self):
        """Test valid CID-10 codes with decimal."""
        assert validate_cid10("J18.0") is True
        assert validate_cid10("A01.1") is True
        assert validate_cid10("M54.5") is True

    def test_valid_cid10_with_two_decimal(self):
        """Test valid CID-10 codes with two decimal places."""
        assert validate_cid10("J18.01") is True
        assert validate_cid10("A01.10") is True

    def test_valid_cid10_lowercase(self):
        """Test valid CID-10 codes in lowercase."""
        assert validate_cid10("j18") is True
        assert validate_cid10("j18.0") is True

    def test_valid_cid10_whitespace(self):
        """Test CID-10 codes with whitespace."""
        assert validate_cid10("  J18  ") is True

    def test_invalid_cid10_numbers_only(self):
        """Test invalid CID-10 with numbers only."""
        assert validate_cid10("123") is False
        assert validate_cid10("123.4") is False

    def test_invalid_cid10_letter_only(self):
        """Test invalid CID-10 with letter only."""
        assert validate_cid10("J") is False
        assert validate_cid10("JA") is False

    def test_invalid_cid10_wrong_format(self):
        """Test invalid CID-10 with wrong format."""
        assert validate_cid10("J1") is False  # Only one digit
        assert validate_cid10("J123") is False  # Three digits
        assert validate_cid10("J18.") is False  # Empty decimal
        assert validate_cid10("J18.123") is False  # Three decimal places

    def test_invalid_cid10_special_chars(self):
        """Test invalid CID-10 with special characters."""
        assert validate_cid10("J-18") is False
        assert validate_cid10("J18_0") is False

    def test_invalid_cid10_empty(self):
        """Test empty CID-10."""
        assert validate_cid10("") is False

    def test_invalid_cid10_none(self):
        """Test None CID-10."""
        assert validate_cid10(None) is False

    def test_is_valid_cid10_alias(self):
        """Test is_valid_cid10 is alias for validate_cid10."""
        assert is_valid_cid10("J18") is True
        assert is_valid_cid10("invalid") is False


# =============================================================================
# CID-10 Chapters Tests
# =============================================================================


class TestCID10Chapters:
    """Tests for CID-10 chapter lookups."""

    def test_cid10_chapters_constant(self):
        """Test CID10_CHAPTERS constant."""
        assert "A00-B99" in CID10_CHAPTERS
        assert "I00-I99" in CID10_CHAPTERS
        assert len(CID10_CHAPTERS) == 21

    def test_get_cid10_chapter_infectious(self):
        """Test getting chapter for infectious diseases."""
        chapter = get_cid10_chapter("A01")
        assert "Infectious" in chapter

    def test_get_cid10_chapter_respiratory(self):
        """Test getting chapter for respiratory diseases."""
        chapter = get_cid10_chapter("J18")
        assert "Respiratory" in chapter

    def test_get_cid10_chapter_circulatory(self):
        """Test getting chapter for circulatory diseases."""
        chapter = get_cid10_chapter("I10")
        assert "Circulatory" in chapter

    def test_get_cid10_chapter_with_decimal(self):
        """Test getting chapter for code with decimal."""
        chapter = get_cid10_chapter("J18.0")
        assert "Respiratory" in chapter

    def test_get_cid10_chapter_lowercase(self):
        """Test getting chapter with lowercase code."""
        chapter = get_cid10_chapter("j18")
        assert "Respiratory" in chapter

    def test_get_cid10_chapter_invalid(self):
        """Test getting chapter for invalid code."""
        assert get_cid10_chapter("invalid") is None

    def test_get_cid10_chapter_edge_cases(self):
        """Test getting chapter for edge case codes."""
        # First chapter
        assert get_cid10_chapter("A00") is not None
        # Last chapter
        assert get_cid10_chapter("Z99") is not None
        # Chapter boundary
        assert get_cid10_chapter("B99") is not None
        assert get_cid10_chapter("C00") is not None


# =============================================================================
# CRM Validation Tests
# =============================================================================


class TestCRMValidation:
    """Tests for CRM validation."""

    def test_valid_crm_with_uf(self):
        """Test valid CRM with UF."""
        assert validate_crm("12345-MG") is True
        assert validate_crm("123456SP") is True
        assert validate_crm("12345/RJ") is True

    def test_valid_crm_without_uf(self):
        """Test valid CRM without UF."""
        assert validate_crm("123456") is True
        assert validate_crm("1") is True
        assert validate_crm("999999") is True

    def test_valid_crm_with_expected_uf(self):
        """Test valid CRM with expected UF."""
        assert validate_crm("12345-MG", uf="MG") is True
        assert validate_crm("123456SP", uf="SP") is True

    def test_invalid_crm_wrong_uf(self):
        """Test invalid CRM with wrong UF."""
        assert validate_crm("12345-MG", uf="SP") is False

    def test_invalid_crm_bad_uf(self):
        """Test invalid CRM with bad UF code."""
        assert validate_crm("12345-XX") is False

    def test_invalid_crm_expected_bad_uf(self):
        """Test invalid CRM with bad expected UF."""
        assert validate_crm("123456", uf="XX") is False

    def test_invalid_crm_too_long(self):
        """Test invalid CRM with too many digits."""
        assert validate_crm("1234567") is False
        assert validate_crm("1234567MG") is False

    def test_invalid_crm_letters_in_number(self):
        """Test invalid CRM with letters in number."""
        assert validate_crm("ABC123-MG") is False

    def test_invalid_crm_empty(self):
        """Test empty CRM."""
        assert validate_crm("") is False

    def test_invalid_crm_none(self):
        """Test None CRM."""
        assert validate_crm(None) is False

    def test_is_valid_crm_alias(self):
        """Test is_valid_crm is alias for validate_crm."""
        assert is_valid_crm("12345-MG") is True
        assert is_valid_crm("invalid") is False


# =============================================================================
# CRM Cleaning Tests
# =============================================================================


class TestCRMCleaning:
    """Tests for CRM cleaning."""

    def test_clean_crm_simple(self):
        """Test simple CRM cleaning."""
        assert clean_crm("12345-MG") == "12345MG"
        assert clean_crm("12345 MG") == "12345MG"

    def test_clean_crm_special_chars(self):
        """Test CRM cleaning with special characters."""
        assert clean_crm("CRM/12345-MG") == "CRM12345MG"
        assert clean_crm("123.456-MG") == "123456MG"

    def test_clean_crm_none(self):
        """Test cleaning None CRM."""
        assert clean_crm(None) == ""


# =============================================================================
# CRM Formatting Tests
# =============================================================================


class TestCRMFormatting:
    """Tests for CRM formatting."""

    def test_format_crm_with_uf(self):
        """Test formatting CRM with UF."""
        assert format_crm("12345MG") == "CRM/MG 12345"
        assert format_crm("123456SP") == "CRM/SP 123456"

    def test_format_crm_with_provided_uf(self):
        """Test formatting CRM with provided UF."""
        assert format_crm("123456", uf="RJ") == "CRM/RJ 123456"

    def test_format_crm_without_uf(self):
        """Test formatting CRM without UF."""
        assert format_crm("123456") == "CRM 123456"

    def test_format_crm_already_formatted(self):
        """Test formatting already formatted CRM."""
        # The format function cleans and re-formats
        result = format_crm("CRM/MG 12345")
        # Should produce valid CRM format
        assert result.startswith("CRM")


# =============================================================================
# Medication Units Tests
# =============================================================================


class TestMedicationUnits:
    """Tests for medication units constant."""

    def test_medication_units_exist(self):
        """Test that medication units exist."""
        assert "mg" in MEDICATION_UNITS
        assert "ml" in MEDICATION_UNITS
        assert "ui" in MEDICATION_UNITS
        assert "%" in MEDICATION_UNITS

    def test_medication_units_mass(self):
        """Test mass units."""
        assert "mg" in MEDICATION_UNITS
        assert "g" in MEDICATION_UNITS
        assert "mcg" in MEDICATION_UNITS
        assert "kg" in MEDICATION_UNITS

    def test_medication_units_volume(self):
        """Test volume units."""
        assert "ml" in MEDICATION_UNITS
        assert "l" in MEDICATION_UNITS
        assert "cc" in MEDICATION_UNITS


# =============================================================================
# Medication Dosage Tests
# =============================================================================


class TestMedicationDosage:
    """Tests for medication dosage validation."""

    def test_valid_dosage_mg(self):
        """Test valid dosage in mg."""
        is_valid, parsed = validate_medication_dosage("500mg")
        assert is_valid is True
        assert parsed["value"] == 500.0
        assert parsed["unit"] == "mg"
        assert parsed["original"] == "500mg"

    def test_valid_dosage_ml(self):
        """Test valid dosage in ml."""
        is_valid, parsed = validate_medication_dosage("10 ml")
        assert is_valid is True
        assert parsed["value"] == 10.0
        assert parsed["unit"] == "ml"

    def test_valid_dosage_decimal(self):
        """Test valid dosage with decimal."""
        is_valid, parsed = validate_medication_dosage("0.5mg")
        assert is_valid is True
        assert parsed["value"] == 0.5

    def test_valid_dosage_comma_decimal(self):
        """Test valid dosage with comma decimal."""
        is_valid, parsed = validate_medication_dosage("0,5mg")
        assert is_valid is True
        assert parsed["value"] == 0.5

    def test_valid_dosage_capsule(self):
        """Test valid dosage in capsules."""
        is_valid, parsed = validate_medication_dosage("2comp")
        assert is_valid is True
        assert parsed["value"] == 2.0
        assert parsed["unit"] == "comp"

    def test_valid_dosage_percentage(self):
        """Test valid dosage with percentage."""
        is_valid, parsed = validate_medication_dosage("5%")
        assert is_valid is True
        assert parsed["value"] == 5.0
        assert parsed["unit"] == "%"

    def test_invalid_dosage_no_unit(self):
        """Test invalid dosage without unit."""
        is_valid, parsed = validate_medication_dosage("500")
        assert is_valid is False
        assert parsed is None

    def test_invalid_dosage_unknown_unit(self):
        """Test invalid dosage with unknown unit."""
        is_valid, parsed = validate_medication_dosage("500xyz")
        assert is_valid is False
        assert parsed is None

    def test_invalid_dosage_empty(self):
        """Test empty dosage."""
        is_valid, parsed = validate_medication_dosage("")
        assert is_valid is False
        assert parsed is None

    def test_invalid_dosage_none(self):
        """Test None dosage."""
        is_valid, parsed = validate_medication_dosage(None)
        assert is_valid is False
        assert parsed is None

    def test_dosage_with_max_value(self):
        """Test dosage with maximum value."""
        is_valid, parsed = validate_medication_dosage("500mg", max_value=1000)
        assert is_valid is True

    def test_dosage_exceeds_max_value(self):
        """Test dosage exceeding maximum value."""
        is_valid, parsed = validate_medication_dosage("1500mg", max_value=1000)
        assert is_valid is False
        assert parsed is None


# =============================================================================
# Medication Frequency Tests
# =============================================================================


class TestMedicationFrequency:
    """Tests for medication frequency validation."""

    def test_valid_frequency_8h(self):
        """Test valid 8/8h frequency."""
        is_valid, parsed = validate_medication_frequency("8/8h")
        assert is_valid is True
        assert parsed["times_per_day"] == 3
        assert parsed["interval_hours"] == 8.0

    def test_valid_frequency_12h(self):
        """Test valid 12/12h frequency."""
        is_valid, parsed = validate_medication_frequency("12/12h")
        assert is_valid is True
        assert parsed["times_per_day"] == 2
        assert parsed["interval_hours"] == 12.0

    def test_valid_frequency_6h(self):
        """Test valid 6/6h frequency."""
        is_valid, parsed = validate_medication_frequency("6/6h")
        assert is_valid is True
        assert parsed["times_per_day"] == 4

    def test_valid_frequency_per_day(self):
        """Test valid x ao dia frequency."""
        is_valid, parsed = validate_medication_frequency("3x ao dia")
        assert is_valid is True
        assert parsed["times_per_day"] == 3
        assert parsed["interval_hours"] == 8.0

    def test_valid_frequency_por_dia(self):
        """Test valid x por dia frequency."""
        is_valid, parsed = validate_medication_frequency("2 por dia")
        assert is_valid is True
        assert parsed["times_per_day"] == 2
        assert parsed["interval_hours"] == 12.0

    def test_valid_frequency_slash_dia(self):
        """Test valid x/dia frequency."""
        is_valid, parsed = validate_medication_frequency("4/dia")
        assert is_valid is True
        assert parsed["times_per_day"] == 4

    def test_valid_frequency_once_daily(self):
        """Test valid once daily frequency."""
        is_valid, parsed = validate_medication_frequency("1x ao dia")
        assert is_valid is True
        assert parsed["times_per_day"] == 1
        assert parsed["interval_hours"] == 24.0

    def test_invalid_frequency_format(self):
        """Test invalid frequency format."""
        is_valid, parsed = validate_medication_frequency("invalid")
        assert is_valid is False
        assert parsed is None

    def test_invalid_frequency_zero(self):
        """Test invalid zero frequency."""
        is_valid, parsed = validate_medication_frequency("0x ao dia")
        assert is_valid is False
        assert parsed is None

    def test_invalid_frequency_too_high(self):
        """Test invalid too high frequency."""
        is_valid, parsed = validate_medication_frequency("25x ao dia")
        assert is_valid is False
        assert parsed is None

    def test_invalid_frequency_empty(self):
        """Test empty frequency."""
        is_valid, parsed = validate_medication_frequency("")
        assert is_valid is False
        assert parsed is None

    def test_invalid_frequency_none(self):
        """Test None frequency."""
        is_valid, parsed = validate_medication_frequency(None)
        assert is_valid is False
        assert parsed is None


# =============================================================================
# BMI Calculation Tests
# =============================================================================


class TestBMICalculation:
    """Tests for BMI calculation."""

    def test_bmi_normal(self):
        """Test normal BMI calculation."""
        bmi = calculate_bmi(70, 175)  # 70kg, 1.75m
        assert 22 < bmi < 23

    def test_bmi_underweight(self):
        """Test underweight BMI calculation."""
        bmi = calculate_bmi(50, 175)
        assert bmi < 18.5

    def test_bmi_overweight(self):
        """Test overweight BMI calculation."""
        bmi = calculate_bmi(85, 175)
        assert 25 < bmi < 30

    def test_bmi_obese(self):
        """Test obese BMI calculation."""
        bmi = calculate_bmi(100, 175)
        assert bmi >= 30

    def test_bmi_invalid_zero_weight(self):
        """Test BMI with zero weight."""
        assert calculate_bmi(0, 175) is None

    def test_bmi_invalid_zero_height(self):
        """Test BMI with zero height."""
        assert calculate_bmi(70, 0) is None

    def test_bmi_invalid_negative(self):
        """Test BMI with negative values."""
        assert calculate_bmi(-70, 175) is None
        assert calculate_bmi(70, -175) is None

    def test_bmi_very_tall(self):
        """Test BMI for very tall person."""
        bmi = calculate_bmi(90, 210)
        assert bmi is not None
        assert bmi > 0

    def test_bmi_rounding(self):
        """Test BMI rounding to 2 decimal places."""
        bmi = calculate_bmi(70, 175)
        # Should have at most 2 decimal places
        assert bmi == round(bmi, 2)


# =============================================================================
# BMI Classification Tests
# =============================================================================


class TestBMIClassification:
    """Tests for BMI classification."""

    def test_classify_bmi_severe_underweight(self):
        """Test severe underweight classification."""
        assert classify_bmi(15) == "severe_underweight"
        assert classify_bmi(15.9) == "severe_underweight"

    def test_classify_bmi_moderate_underweight(self):
        """Test moderate underweight classification."""
        assert classify_bmi(16) == "moderate_underweight"
        assert classify_bmi(16.9) == "moderate_underweight"

    def test_classify_bmi_mild_underweight(self):
        """Test mild underweight classification."""
        assert classify_bmi(17) == "mild_underweight"
        assert classify_bmi(18.4) == "mild_underweight"

    def test_classify_bmi_normal(self):
        """Test normal classification."""
        assert classify_bmi(18.5) == "normal"
        assert classify_bmi(22) == "normal"
        assert classify_bmi(24.9) == "normal"

    def test_classify_bmi_overweight(self):
        """Test overweight classification."""
        assert classify_bmi(25) == "overweight"
        assert classify_bmi(27) == "overweight"
        assert classify_bmi(29.9) == "overweight"

    def test_classify_bmi_obese_class_1(self):
        """Test obese class 1 classification."""
        assert classify_bmi(30) == "obese_class_1"
        assert classify_bmi(32) == "obese_class_1"
        assert classify_bmi(34.9) == "obese_class_1"

    def test_classify_bmi_obese_class_2(self):
        """Test obese class 2 classification."""
        assert classify_bmi(35) == "obese_class_2"
        assert classify_bmi(37) == "obese_class_2"
        assert classify_bmi(39.9) == "obese_class_2"

    def test_classify_bmi_obese_class_3(self):
        """Test obese class 3 classification."""
        assert classify_bmi(40) == "obese_class_3"
        assert classify_bmi(45) == "obese_class_3"
        assert classify_bmi(50) == "obese_class_3"

    def test_classify_bmi_invalid_none(self):
        """Test classification with None."""
        assert classify_bmi(None) is None

    def test_classify_bmi_invalid_zero(self):
        """Test classification with zero."""
        assert classify_bmi(0) is None

    def test_classify_bmi_invalid_negative(self):
        """Test classification with negative."""
        assert classify_bmi(-5) is None


# =============================================================================
# Weight Validation Tests
# =============================================================================


class TestWeightValidation:
    """Tests for weight validation."""

    def test_valid_weight_adult(self):
        """Test valid adult weight."""
        assert validate_weight(70) is True
        assert validate_weight(50) is True
        assert validate_weight(150) is True

    def test_valid_weight_child(self):
        """Test valid child weight."""
        assert validate_weight(10) is True
        assert validate_weight(5) is True

    def test_invalid_weight_too_low(self):
        """Test invalid weight too low."""
        assert validate_weight(1) is False
        assert validate_weight(0) is False
        assert validate_weight(-10) is False

    def test_invalid_weight_too_high(self):
        """Test invalid weight too high."""
        assert validate_weight(501) is False
        assert validate_weight(600) is False

    def test_valid_weight_boundary(self):
        """Test weight at boundary values."""
        assert validate_weight(2) is True  # Minimum
        assert validate_weight(500) is True  # Maximum


# =============================================================================
# Height Validation Tests
# =============================================================================


class TestHeightValidation:
    """Tests for height validation."""

    def test_valid_height_adult(self):
        """Test valid adult height."""
        assert validate_height(170) is True
        assert validate_height(160) is True
        assert validate_height(180) is True

    def test_valid_height_short(self):
        """Test valid short height."""
        assert validate_height(100) is True
        assert validate_height(50) is True

    def test_valid_height_tall(self):
        """Test valid tall height."""
        assert validate_height(200) is True
        assert validate_height(250) is True

    def test_invalid_height_too_low(self):
        """Test invalid height too low."""
        assert validate_height(49) is False
        assert validate_height(0) is False
        assert validate_height(-10) is False

    def test_invalid_height_too_high(self):
        """Test invalid height too high."""
        assert validate_height(281) is False
        assert validate_height(300) is False

    def test_valid_height_boundary(self):
        """Test height at boundary values."""
        assert validate_height(50) is True  # Minimum
        assert validate_height(280) is True  # Maximum
