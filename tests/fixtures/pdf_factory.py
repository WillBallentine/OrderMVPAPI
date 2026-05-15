"""
Programmatic PDF generation for tests using PyMuPDF (fitz).

Two modes:
  - text_pdf(lines)  → embedded text; exercises the pdfplumber path
  - image_pdf(lines) → text rendered to an image then re-embedded as a raster page;
                       exercises the OCR path (pdfplumber gets nothing, falls back to
                       Tesseract)
"""
import fitz


def text_pdf(lines: list[str]) -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # US Letter
    y = 72.0
    for line in lines:
        page.insert_text((72, y), line, fontsize=12, color=(0, 0, 0))
        y += 18.0
    data = doc.tobytes()
    doc.close()
    return data


def image_pdf(lines: list[str], dpi: int = 200) -> bytes:
    """
    Create an image-only PDF:
      - Build a text PDF from the lines.
      - Render each page to a raster image at `dpi`.
      - Pack those images into a new PDF with no text layer.
    """
    src_bytes = text_pdf(lines)
    src = fitz.open(stream=src_bytes, filetype="pdf")

    out = fitz.open()
    scale = dpi / 72.0
    mat = fitz.Matrix(scale, scale)

    for page in src:
        pix = page.get_pixmap(matrix=mat, alpha=False)
        png_bytes = pix.tobytes("png")

        w_pt = page.rect.width
        h_pt = page.rect.height
        img_page = out.new_page(width=w_pt, height=h_pt)
        img_page.insert_image(img_page.rect, stream=png_bytes)

    data = out.tobytes()
    src.close()
    out.close()
    return data
