from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class InvalidPdfError(ValueError):
    pass


class EmptyPdfError(ValueError):
    pass


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


def extract_pdf_pages(pdf_bytes: bytes) -> list[PageText]:
    """Extract text page-by-page so every later chunk keeps its source page."""
    if not pdf_bytes:
        raise InvalidPdfError("The uploaded file is empty.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        if not reader.pages:
            raise EmptyPdfError("The PDF contains no pages.")

        pages = [
            PageText(page_number=index + 1, text=(page.extract_text() or "").strip())
            for index, page in enumerate(reader.pages)
        ]
    except EmptyPdfError:
        raise
    except (PdfReadError, EOFError, ValueError, OSError) as exc:
        raise InvalidPdfError("The uploaded file is not a readable PDF.") from exc

    if not any(page.text for page in pages):
        raise EmptyPdfError("The PDF does not contain extractable text.")
    return pages
