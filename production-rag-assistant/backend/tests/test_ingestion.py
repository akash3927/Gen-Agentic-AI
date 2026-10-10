import pytest
from pypdf import PdfWriter

from app.services.chunker import chunk_pages
from app.services.pdf_extractor import EmptyPdfError, InvalidPdfError, PageText, extract_pdf_pages


def test_extraction_and_chunk_metadata(pdf_factory):
    pages = extract_pdf_pages(pdf_factory("First page", "Second page"))
    chunks = chunk_pages(pages, chunk_size=50, chunk_overlap=10)
    assert [page.page_number for page in pages] == [1, 2]
    assert [chunk.page_number for chunk in chunks] == [1, 2]


def test_invalid_pdf():
    with pytest.raises(InvalidPdfError):
        extract_pdf_pages(b"not a pdf")


def test_empty_pdf():
    stream = __import__("io").BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(stream)
    with pytest.raises(EmptyPdfError):
        extract_pdf_pages(stream.getvalue())


def test_chunk_overlap():
    chunks = chunk_pages([PageText(1, "a" * 120)], 50, 10)
    assert [len(chunk.text) for chunk in chunks] == [50, 50, 40]
    assert chunks[0].text[-10:] == chunks[1].text[:10]
