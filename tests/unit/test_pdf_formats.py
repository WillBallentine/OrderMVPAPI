"""
Tests for PDF extraction across varied document formats and layouts.

Each test generates a synthetic PDF via the factory and runs the full
extract_patient_info pipeline so that both the text and OCR paths are exercised
end-to-end without needing real patient documents.
"""
import pytest
from tests.fixtures.pdf_factory import text_pdf, image_pdf
from app.services.pdf_extractor import extract_patient_info


# ── helpers ───────────────────────────────────────────────────────────────────

def run(lines: list[str], *, via_ocr: bool = False) -> dict:
    factory = image_pdf if via_ocr else text_pdf
    return extract_patient_info(factory(lines))


# ── text-based PDF formats ────────────────────────────────────────────────────

class TestInlineColonFormat:
    def test_patient_name_and_dob(self):
        r = run(["Patient Name: Jane Smith", "DOB: 03/22/1975"])
        assert r["patient_first_name"] == "Jane"
        assert r["patient_last_name"] == "Smith"
        assert r["patient_dob"] == "03/22/1975"
        assert r["extraction_confidence"] == "high"

    def test_separate_first_last_fields(self):
        r = run(["First Name: Alice", "Last Name: Walker", "Date of Birth: 1990-06-15"])
        assert r["patient_first_name"] == "Alice"
        assert r["patient_last_name"] == "Walker"
        assert r["patient_dob"] == "1990-06-15"

    def test_last_comma_first_name_format(self):
        r = run(["Patient Name: Curie, Marie", "DOB: 12/05/1900"])
        assert r["patient_first_name"] == "Marie"
        assert r["patient_last_name"] == "Curie"

    def test_beneficiary_name_label(self):
        r = run(["Beneficiary Name: Robert Frost", "DOB: 03/26/1874"])
        assert r["patient_first_name"] == "Robert"
        assert r["patient_last_name"] == "Frost"

    def test_member_name_label(self):
        r = run(["Member Name: Ada Lovelace", "Date of Birth: 12/10/1815"])
        assert r["patient_first_name"] == "Ada"
        assert r["patient_last_name"] == "Lovelace"

    def test_dob_iso_format(self):
        r = run(["Patient Name: John Doe", "DOB: 1985-01-15"])
        assert r["patient_dob"] == "1985-01-15"

    def test_dob_written_month(self):
        r = run(["Patient Name: John Doe", "Date of Birth: January 15, 1985"])
        assert r["patient_dob"] == "January 15, 1985"

    def test_dob_abbreviated_month(self):
        r = run(["Patient Name: John Doe", "DOB: Jan 15, 1985"])
        assert r["patient_dob"] == "Jan 15, 1985"

    def test_noise_lines_around_data(self):
        r = run([
            "Acme Medical Center",
            "123 Main Street, Springfield",
            "Prescription - Standard Written Order",
            "",
            "Patient Name: George Burns",
            "Insurance ID: 987654321",
            "DOB: 01/20/1896",
            "Diagnosis: Extreme longevity",
        ])
        assert r["patient_first_name"] == "George"
        assert r["patient_last_name"] == "Burns"
        assert r["patient_dob"] == "01/20/1896"

    def test_prescriber_name_not_confused_with_patient(self):
        r = run([
            "Patient Name: Marie Curie",
            "DOB: 12/05/1900",
            "Prescriber Name: Gregory House MD",
            "Prescriber NPI: 1234567890",
        ])
        assert r["patient_first_name"] == "Marie"
        assert r["patient_last_name"] == "Curie"


class TestHeaderAboveValueFormat:
    def test_name_below_label(self):
        r = run(["Patient Name", "Jane Smith", "Date of Birth", "03/22/1975"])
        assert r["patient_first_name"] == "Jane"
        assert r["patient_last_name"] == "Smith"
        assert r["patient_dob"] == "03/22/1975"

    def test_dob_label_then_date(self):
        r = run(["patient date of birth", "12/05/1900"])
        assert r["patient_dob"] == "12/05/1900"

    def test_address_line_after_name_is_skipped(self):
        r = run([
            "Patient Name",
            "John Doe",
            "123 Elm St",
            "DOB: 04/01/1960",
        ])
        assert r["patient_first_name"] == "John"
        assert r["patient_last_name"] == "Doe"


class TestTwoColumnMergedFormat:
    def test_merged_header_splits_correctly(self):
        r = run([
            "Patient Name and Address Patient Date of Birth",
            "Marie Curie 12/05/1900",
            "218 Forest Hills Ave",
        ])
        assert r["patient_first_name"] == "Marie"
        assert r["patient_last_name"] == "Curie"
        assert r["patient_dob"] == "12/05/1900"


class TestPartialData:
    def test_only_name_found(self):
        r = run(["Patient Name: Solo Name"])
        assert r["patient_first_name"] == "Solo"
        assert r["extraction_confidence"] in ("low", "medium")

    def test_only_dob_found(self):
        r = run(["DOB: 01/01/2000"])
        assert r["patient_dob"] == "01/01/2000"
        assert r["extraction_confidence"] == "low"

    def test_nothing_found(self):
        r = run(["Diagnosis: Osteoarthritis", "Treatment: Physical therapy"])
        assert r["extraction_confidence"] == "none"


# ── image-based PDF formats (OCR path) ───────────────────────────────────────

@pytest.mark.slow
class TestOCRPath:
    """
    These tests render text to an image-only PDF, forcing the Tesseract OCR path.
    Marked slow because OCR takes a few seconds per page.
    """

    def test_inline_colon_via_ocr(self):
        r = run(["Patient Name: John Doe", "DOB: 04/15/1970"], via_ocr=True)
        assert r["patient_first_name"] == "John"
        assert r["patient_last_name"] == "Doe"
        assert r["patient_dob"] == "04/15/1970"
        assert r["extraction_confidence"] == "high"

    def test_separate_fields_via_ocr(self):
        r = run(["First Name: Alice", "Last Name: Walker", "DOB: 06/15/1990"], via_ocr=True)
        assert r["patient_first_name"] == "Alice"
        assert r["patient_last_name"] == "Walker"
        assert r["patient_dob"] == "06/15/1990"

    def test_multiline_document_via_ocr(self):
        r = run([
            "Medical Center",
            "Patient Name: Robert Plant",
            "Date of Birth: 08/20/1948",
            "Insurance: Blue Cross",
        ], via_ocr=True)
        assert r["patient_first_name"] == "Robert"
        assert r["patient_last_name"] == "Plant"
