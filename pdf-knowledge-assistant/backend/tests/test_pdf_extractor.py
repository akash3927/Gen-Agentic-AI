import pytest
from pypdf import PdfWriter

from app.services.pdf_extractor import EmptyPdfError, InvalidPdfError, extract_pdf_pages


def test_extracts_text_and_preserves_page_numbers(pdf_factory):
    pages = extract_pdf_pages(pdf_factory("First page", "Second page"))
    assert [(page.page_number, page.text) for page in pages] == [
        (1, "First page"),
        (2, "Second page"),
    ]


def test_rejects_invalid_pdf():
    with pytest.raises(InvalidPdfError):
        extract_pdf_pages(b"this is not a pdf")


def test_rejects_pdf_without_extractable_text():
    stream = __import__("io").BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(stream)
    with pytest.raises(EmptyPdfError):
        extract_pdf_pages(stream.getvalue())
