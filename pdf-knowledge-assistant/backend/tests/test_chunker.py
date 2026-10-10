import pytest

from app.services.chunker import chunk_pages
from app.services.pdf_extractor import PageText


def test_chunking_overlap_and_metadata():
    chunks = chunk_pages([PageText(3, "A" * 120)], chunk_size=50, chunk_overlap=10)
    assert [len(chunk.text) for chunk in chunks] == [50, 50, 40]
    assert [chunk.page_number for chunk in chunks] == [3, 3, 3]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert chunks[0].text[-10:] == chunks[1].text[:10]


def test_chunk_settings_are_validated():
    with pytest.raises(ValueError):
        chunk_pages([], chunk_size=100, chunk_overlap=100)
