"""Unit tests for the PDF extractor helper functions."""
import pytest
from app.services.pdf_extractor import (
    _colon_inline,
    _colon_inline_dob,
    _two_column_extract,
    _next_line_name,
    _next_line_dob,
    _split_full_name,
    _is_likely_name,
    _confidence,
    extract_patient_info,
    FULL_NAME_LABELS,
    FIRST_NAME_LABELS,
    LAST_NAME_LABELS,
    DOB_LABELS,
)


# ── _split_full_name ──────────────────────────────────────────────────────────

class TestSplitFullName:
    def test_space_separated(self):
        assert _split_full_name("Marie Curie") == ("Marie", "Curie")

    def test_three_part_name(self):
        fn, ln = _split_full_name("Mary Jo Smith")
        assert fn == "Mary"
        assert ln == "Smith"  # middle name discarded

    def test_comma_separated_last_first(self):
        assert _split_full_name("Curie, Marie") == ("Marie", "Curie")

    def test_single_name(self):
        fn, ln = _split_full_name("Madonna")
        assert fn == "Madonna"
        assert ln is None

    def test_strips_whitespace(self):
        assert _split_full_name("  John   Doe  ") == ("John", "Doe")


# ── _is_likely_name ───────────────────────────────────────────────────────────

class TestIsLikelyName:
    def test_valid_two_part(self):
        assert _is_likely_name("Marie Curie") is True

    def test_valid_single(self):
        assert _is_likely_name("Marie") is True

    def test_rejects_digits(self):
        assert _is_likely_name("Marie Curie 12/05/1900") is False

    def test_rejects_prescriber_token(self):
        assert _is_likely_name("Arjun Raj Prescriber") is False

    def test_rejects_empty(self):
        assert _is_likely_name("") is False

    def test_rejects_too_long(self):
        assert _is_likely_name("A" * 61) is False

    def test_rejects_five_words(self):
        assert _is_likely_name("one two three four five") is False


# ── _confidence ───────────────────────────────────────────────────────────────

class TestConfidence:
    def test_all_found(self):
        assert _confidence("Marie", "Curie", "12/05/1900") == "high"

    def test_two_found(self):
        assert _confidence("Marie", "Curie", None) == "medium"

    def test_one_found(self):
        assert _confidence(None, None, "12/05/1900") == "low"

    def test_none_found(self):
        assert _confidence(None, None, None) == "none"


# ── _colon_inline ─────────────────────────────────────────────────────────────

class TestColonInline:
    def test_patient_name_colon(self):
        lines = ["Patient Name: Marie Curie"]
        result = _colon_inline(lines, FULL_NAME_LABELS)
        assert result == "Marie Curie"

    def test_case_insensitive_label(self):
        lines = ["PATIENT NAME: Marie Curie"]
        result = _colon_inline(lines, FULL_NAME_LABELS)
        assert result == "Marie Curie"

    def test_preserves_value_casing(self):
        lines = ["Patient Name: Marie Curie"]
        result = _colon_inline(lines, FULL_NAME_LABELS)
        assert result == "Marie Curie"  # not lowercase

    def test_first_name_colon(self):
        lines = ["First Name: John"]
        assert _colon_inline(lines, FIRST_NAME_LABELS) == "John"

    def test_last_name_colon(self):
        lines = ["Last Name: Doe"]
        assert _colon_inline(lines, LAST_NAME_LABELS) == "Doe"

    def test_no_colon_returns_none(self):
        lines = ["Patient Name Marie Curie"]
        assert _colon_inline(lines, FULL_NAME_LABELS) is None

    def test_skips_non_matching_lines(self):
        lines = ["Random line", "Another line", "Patient Name: Jane Smith"]
        assert _colon_inline(lines, FULL_NAME_LABELS) == "Jane Smith"


# ── _colon_inline_dob ─────────────────────────────────────────────────────────

class TestColonInlineDob:
    def test_dob_mm_dd_yyyy(self):
        assert _colon_inline_dob(["DOB: 12/05/1900"]) == "12/05/1900"

    def test_patient_date_of_birth(self):
        assert _colon_inline_dob(["Patient Date of Birth: 01-15-1985"]) == "01-15-1985"

    def test_iso_format(self):
        assert _colon_inline_dob(["Date of Birth: 1985-01-15"]) == "1985-01-15"

    def test_written_month(self):
        result = _colon_inline_dob(["DOB: January 15, 1985"])
        assert result == "January 15, 1985"

    def test_no_dob_label_returns_none(self):
        assert _colon_inline_dob(["Name: Marie Curie"]) is None

    def test_no_date_value_returns_raw(self):
        # Label present but value is not a recognizable date — returns raw string
        result = _colon_inline_dob(["DOB: unknown"])
        assert result == "unknown"


# ── _two_column_extract ───────────────────────────────────────────────────────

class TestTwoColumnExtract:
    def test_scanned_fax_layout(self):
        lines = [
            "Patient Name and Address Patient Date of Birth",
            "Marie Curie 12/05/1900",
        ]
        fn, ln, dob = _two_column_extract(lines)
        assert fn == "Marie"
        assert ln == "Curie"
        assert dob == "12/05/1900"

    def test_no_merged_header_returns_none(self):
        lines = ["Patient Name: Marie Curie", "DOB: 12/05/1900"]
        fn, ln, dob = _two_column_extract(lines)
        assert fn is None and ln is None and dob is None

    def test_value_line_has_no_date(self):
        lines = [
            "Patient Name and Address Patient Date of Birth",
            "Marie Curie",  # no date on this line
        ]
        fn, ln, dob = _two_column_extract(lines)
        assert fn is None and ln is None and dob is None


# ── _next_line_name / _next_line_dob ─────────────────────────────────────────

class TestNextLine:
    def test_next_line_name_exact_label(self):
        lines = ["patient name", "Marie Curie"]
        result = _next_line_name(lines, FULL_NAME_LABELS)
        assert result == "Marie Curie"

    def test_next_line_name_skips_bad_candidate(self):
        lines = ["patient name", "123 Main St"]  # address, not a name
        assert _next_line_name(lines, FULL_NAME_LABELS) is None

    def test_next_line_dob_finds_date(self):
        lines = ["patient date of birth", "12/05/1900"]
        assert _next_line_dob(lines) == "12/05/1900"

    def test_next_line_dob_no_date_returns_none(self):
        lines = ["patient date of birth", "not a date"]
        assert _next_line_dob(lines) is None


# ── Full pipeline regression (requires sample PDF) ───────────────────────────

class TestExtractPatientInfo:
    def test_colon_inline_text_pdf(self):
        """Simulate a clean text-based PDF with inline colon format."""
        from unittest.mock import patch

        fake_lines = [
            "Clinical Summary",
            "Patient Name: Marie Curie",
            "DOB: 12/05/1900",
            "AGE: 124",
        ]

        with patch("app.services.pdf_extractor._get_lines", return_value=fake_lines):
            result = extract_patient_info(b"%PDF-fake")

        assert result["patient_first_name"] == "Marie"
        assert result["patient_last_name"] == "Curie"
        assert result["patient_dob"] == "12/05/1900"
        assert result["extraction_confidence"] == "high"

    def test_two_column_scanned_format(self):
        from unittest.mock import patch

        fake_lines = [
            "Patient Name and Address Patient Date of Birth",
            "John Doe 01/20/1975",
        ]

        with patch("app.services.pdf_extractor._get_lines", return_value=fake_lines):
            result = extract_patient_info(b"%PDF-fake")

        assert result["patient_first_name"] == "John"
        assert result["patient_last_name"] == "Doe"
        assert result["patient_dob"] == "01/20/1975"
        assert result["extraction_confidence"] == "high"

    def test_separate_first_last_fields(self):
        from unittest.mock import patch

        fake_lines = [
            "First Name: Jane",
            "Last Name: Smith",
            "Date of Birth: 1990-06-15",
        ]

        with patch("app.services.pdf_extractor._get_lines", return_value=fake_lines):
            result = extract_patient_info(b"%PDF-fake")

        assert result["patient_first_name"] == "Jane"
        assert result["patient_last_name"] == "Smith"
        assert result["patient_dob"] == "1990-06-15"

    def test_comma_last_first_name(self):
        from unittest.mock import patch

        fake_lines = ["Patient Name: Doe, John", "DOB: 03/22/1960"]

        with patch("app.services.pdf_extractor._get_lines", return_value=fake_lines):
            result = extract_patient_info(b"%PDF-fake")

        assert result["patient_first_name"] == "John"
        assert result["patient_last_name"] == "Doe"

    def test_partial_extraction_returns_medium_confidence(self):
        from unittest.mock import patch

        fake_lines = ["Patient Name: Only Namegiven"]

        with patch("app.services.pdf_extractor._get_lines", return_value=fake_lines):
            result = extract_patient_info(b"%PDF-fake")

        assert result["extraction_confidence"] in ("medium", "low", "high")

    def test_nothing_found_returns_none_confidence(self):
        from unittest.mock import patch

        with patch("app.services.pdf_extractor._get_lines", return_value=["random text"]):
            result = extract_patient_info(b"%PDF-fake")

        assert result["extraction_confidence"] == "none"
        assert result["patient_first_name"] is None
