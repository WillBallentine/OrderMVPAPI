import re
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageOps
from io import BytesIO
from typing import Optional
import os
import platform

# On Windows, help pytesseract find Tesseract if it's not on PATH
if platform.system() == "Windows":
    _tess_candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for _p in _tess_candidates:
        if os.path.exists(_p):
            pytesseract.pytesseract.tesseract_cmd = _p
            break

FULL_NAME_LABELS = [
    "patient name and address",
    "patient name",
    "beneficiary name",
    "member name",
    "subscriber name",
    "enrollee name",
    "patient full name",
    "full name",
    "pt name",
    "pt. name",
    "name",
]

FIRST_NAME_LABELS = [
    "patient first name",
    "first name",
    "firstname",
    "given name",
    "first",
    "fname",
]

LAST_NAME_LABELS = [
    "patient last name",
    "last name",
    "lastname",
    "surname",
    "family name",
    "last",
    "lname",
]

DOB_LABELS = [
    "patient date of birth",
    "date of birth (dob)",
    "date of birth",
    "patient dob",
    "dob",
    "d.o.b.",
    "d.o.b",
    "birth date",
    "birthdate",
    "date of birth (mm/dd/yyyy)",
    "born",
    "birth",
]

DATE_RE = re.compile(
    r"\b("
    r"\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}"
    r"|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}"
    r"|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}"
    r"|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}"
    r")\b",
    re.IGNORECASE,
)

HEADER_TOKENS = re.compile(
    r"\b(prescriber|provider|facility|clinic|hospital|signature|npi|fax)\b",
    re.IGNORECASE,
)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _norm(text: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation used as separators."""
    return re.sub(r"\s+", " ", text).strip().lower()


# Common OCR substitutions: semicolons/pipes misread as colons, etc.
_OCR_ARTIFACT_RE = re.compile(r"[;|]")

def _normalize_ocr_artifacts(text: str) -> str:
    return _OCR_ARTIFACT_RE.sub(":", text)


def _is_likely_name(text: str) -> bool:
    text = _clean(text)
    if not text or len(text) > 60:
        return False
    if HEADER_TOKENS.search(text):
        return False
    if re.search(r"\d", text):
        return False
    parts = text.split()
    return 1 <= len(parts) <= 4


def _split_full_name(full_name: str) -> tuple[Optional[str], Optional[str]]:
    full_name = _clean(full_name)
    if "," in full_name:
        last, _, remainder = full_name.partition(",")
        first_parts = remainder.strip().split()
        return (first_parts[0] if first_parts else None), last.strip()
    parts = full_name.split()
    if len(parts) >= 2:
        return parts[0], parts[-1]
    if len(parts) == 1:
        return parts[0], None
    return None, None


def _colon_inline(lines: list[str], labels: list[str]) -> Optional[str]:
    for line in lines:
        stripped = line.strip()
        n = _norm(stripped)
        for label in labels:
            pattern = rf"^{re.escape(label)}\s*:\s*(.+)"
            m = re.match(pattern, n)
            if m:
                colon_idx = stripped.lower().find(":")
                if colon_idx != -1:
                    value = _clean(stripped[colon_idx + 1:])
                    if value:
                        return value
    return None


def _colon_inline_dob(lines: list[str]) -> Optional[str]:
    for line in lines:
        stripped = line.strip()
        n = _norm(stripped)
        for label in DOB_LABELS:
            pattern = rf"^{re.escape(label)}\s*:\s*(.+)"
            m = re.match(pattern, n)
            if m:
                colon_idx = stripped.lower().find(":")
                if colon_idx != -1:
                    candidate = _clean(stripped[colon_idx + 1:])
                    date_m = DATE_RE.search(candidate)
                    if date_m:
                        return date_m.group(0)
                    if candidate:
                        return candidate
    return None


def _has_any_label(text: str, labels: list[str]) -> bool:
    n = _norm(text)
    return any(label in n for label in labels)


def _two_column_extract(lines: list[str]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    for i, line in enumerate(lines[:-1]):
        has_name_hdr = _has_any_label(line, FULL_NAME_LABELS + FIRST_NAME_LABELS)
        has_dob_hdr = _has_any_label(line, DOB_LABELS)
        if has_name_hdr and has_dob_hdr:
            value_line = _clean(lines[i + 1])
            if not value_line:
                continue
            date_m = DATE_RE.search(value_line)
            if date_m:
                dob = date_m.group(0)
                name_part = _clean(value_line[:date_m.start()])
                if _is_likely_name(name_part):
                    fn, ln = _split_full_name(name_part)
                    return fn, ln, dob
    return None, None, None


def _next_line_name(lines: list[str], labels: list[str]) -> Optional[str]:
    for i, line in enumerate(lines[:-1]):
        n = _norm(line.strip())
        if n in labels:
            candidate = _clean(lines[i + 1])
            if _is_likely_name(candidate):
                return candidate
    return None


def _next_line_dob(lines: list[str]) -> Optional[str]:
    for i, line in enumerate(lines[:-1]):
        n = _norm(line.strip())
        if n in DOB_LABELS:
            candidate = _clean(lines[i + 1])
            date_m = DATE_RE.search(candidate)
            if date_m:
                return date_m.group(0)
    return None


def _scan_for_date(lines: list[str]) -> Optional[str]:
    for line in lines:
        m = DATE_RE.search(line)
        if m:
            return m.group(0)
    return None


def _extract_text_pdfplumber(file_bytes: bytes) -> list[str]:
    lines: list[str] = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines.extend(text.splitlines())
    return lines


def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    """
    Grayscale + autocontrast before OCR.
    Significantly improves accuracy on faded, low-contrast, or noisy scans.
    """
    img = img.convert("L")                   # grayscale
    img = ImageOps.autocontrast(img, cutoff=2)  # normalize brightness/contrast
    return img


def _ocr_page(img: Image.Image) -> str:
    img = _preprocess_for_ocr(img)
    return pytesseract.image_to_string(img, config="--psm 3 --oem 3")


def _extract_text_ocr(file_bytes: bytes) -> list[str]:
    lines: list[str] = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page in doc:
        rotation = page.rotation
        mat = fitz.Matrix(300 / 72, 300 / 72).prerotate(-rotation)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        text = _ocr_page(img)
        lines.extend(text.splitlines())
    doc.close()
    return lines


def _get_lines(file_bytes: bytes) -> list[str]:
    lines = _extract_text_pdfplumber(file_bytes)
    if len([l for l in lines if l.strip()]) >= 3:
        return lines
    raw = _extract_text_ocr(file_bytes)
    return [_normalize_ocr_artifacts(line) for line in raw]


def extract_patient_info(file_bytes: bytes) -> dict:
    lines = _get_lines(file_bytes)

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None

    first_name = _colon_inline(lines, FIRST_NAME_LABELS)
    last_name = _colon_inline(lines, LAST_NAME_LABELS)
    dob = _colon_inline_dob(lines)

    if not first_name or not last_name:
        full_name_inline = _colon_inline(lines, FULL_NAME_LABELS)
        if full_name_inline:
            fn, ln = _split_full_name(full_name_inline)
            first_name = first_name or fn
            last_name = last_name or ln

    if not first_name or not last_name or not dob:
        fn, ln, d = _two_column_extract(lines)
        first_name = first_name or fn
        last_name = last_name or ln
        dob = dob or d

    if not first_name or not last_name:
        full_name_next = _next_line_name(lines, FULL_NAME_LABELS + FIRST_NAME_LABELS)
        if full_name_next:
            fn, ln = _split_full_name(full_name_next)
            first_name = first_name or fn
            last_name = last_name or ln
    if not dob:
        dob = _next_line_dob(lines)

    if not dob:
        dob = _scan_for_date(lines)

    return {
        "patient_first_name": first_name,
        "patient_last_name": last_name,
        "patient_dob": dob,
        "extraction_confidence": _confidence(first_name, last_name, dob),
    }


def _confidence(first: Optional[str], last: Optional[str], dob: Optional[str]) -> str:
    found = sum(1 for v in (first, last, dob) if v)
    return ("none", "low", "medium", "high")[found]
