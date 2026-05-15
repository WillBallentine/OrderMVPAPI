"""Integration tests for the /api/v1/documents/extract endpoint."""
import pytest
from unittest.mock import patch

BASE = "/api/v1/documents/extract"

FAKE_PDF_BYTES = (
    b"%PDF-1.4 fake pdf content for testing"
)


def _make_upload(content: bytes, filename: str = "test.pdf", content_type: str = "application/pdf"):
    return {"file": (filename, content, content_type)}


class TestDocumentExtract:
    def test_requires_auth(self, client):
        resp = client.post(BASE, files=_make_upload(FAKE_PDF_BYTES))
        assert resp.status_code == 401

    def test_rejects_non_pdf_content_type(self, client, auth):
        resp = client.post(
            BASE,
            files={"file": ("test.txt", b"some text", "text/plain")},
            headers=auth,
        )
        assert resp.status_code == 415

    def test_rejects_file_with_wrong_magic_bytes(self, client, auth):
        resp = client.post(
            BASE,
            files={"file": ("evil.pdf", b"not a real pdf", "application/pdf")},
            headers=auth,
        )
        assert resp.status_code == 400

    def test_rejects_oversized_file(self, client, auth):
        big = b"%PDF" + b"x" * (11 * 1024 * 1024)  # 11 MB
        resp = client.post(BASE, files=_make_upload(big), headers=auth)
        assert resp.status_code == 413  # HTTP_413_CONTENT_TOO_LARGE

    def test_successful_extraction_returns_200(self, client, auth):
        fake_result = {
            "patient_first_name": "Marie",
            "patient_last_name": "Curie",
            "patient_dob": "12/05/1900",
            "extraction_confidence": "high",
        }
        with patch("app.routers.documents.extract_patient_info", return_value=fake_result):
            resp = client.post(BASE, files=_make_upload(FAKE_PDF_BYTES), headers=auth)

        assert resp.status_code == 200
        data = resp.json()
        assert data["extracted"]["patient_first_name"] == "Marie"
        assert data["extracted"]["patient_last_name"] == "Curie"
        assert data["extracted"]["patient_dob"] == "12/05/1900"
        assert data["extracted"]["extraction_confidence"] == "high"
        assert data["filename"] == "test.pdf"

    def test_partial_extraction_still_returns_200(self, client, auth):
        partial = {
            "patient_first_name": None,
            "patient_last_name": None,
            "patient_dob": "12/05/1900",
            "extraction_confidence": "low",
        }
        with patch("app.routers.documents.extract_patient_info", return_value=partial):
            resp = client.post(BASE, files=_make_upload(FAKE_PDF_BYTES), headers=auth)

        assert resp.status_code == 200
        assert resp.json()["extracted"]["extraction_confidence"] == "low"


class TestDocumentExtractionRegression:
    """Regression test against the real sample PDF shipped with the repo."""

    def test_sample_pdf_extracts_correctly(self, client, auth, sample_pdf_bytes):
        resp = client.post(
            BASE,
            files={"file": ("sample.pdf", sample_pdf_bytes, "application/pdf")},
            headers=auth,
        )
        assert resp.status_code == 200
        data = resp.json()["extracted"]

        assert data["patient_first_name"] == "Marie"
        assert data["patient_last_name"] == "Curie"
        assert data["patient_dob"] == "12/05/1900"
        assert data["extraction_confidence"] == "high"
