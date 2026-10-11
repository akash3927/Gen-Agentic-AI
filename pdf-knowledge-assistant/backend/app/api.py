from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.models import DocumentResponse, MessageResponse, SearchRequest, SearchResponse
from app.services.document_service import DocumentNotFoundError, DocumentService
from app.services.pdf_extractor import EmptyPdfError, InvalidPdfError

router = APIRouter(prefix="/api")


def get_document_service() -> DocumentService:
    raise RuntimeError("Document service dependency was not configured.")


def _public_document(record: dict) -> dict:
    return {key: value for key, value in record.items() if key != "stored_path"}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    file: Annotated[UploadFile, File()],
    chunk_size: Annotated[int, Form(ge=50, le=20_000)] = 1_000,
    chunk_overlap: Annotated[int, Form(ge=0, le=10_000)] = 200,
    service: DocumentService = Depends(get_document_service),
) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    try:
        record = service.index(
            file.filename, await file.read(), chunk_size, chunk_overlap
        )
        return _public_document(record)
    except (InvalidPdfError, EmptyPdfError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(
    service: DocumentService = Depends(get_document_service),
) -> list[dict]:
    return [_public_document(record) for record in service.list_documents()]


@router.delete("/documents/{document_id}", response_model=MessageResponse)
def delete_document(
    document_id: str, service: DocumentService = Depends(get_document_service)
) -> dict[str, str]:
    try:
        service.delete(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found.") from exc
    return {"message": "Document deleted."}


@router.post("/documents/{document_id}/reindex", response_model=DocumentResponse)
def reindex_document(
    document_id: str,
    chunk_size: Annotated[int | None, Form(ge=50, le=20_000)] = None,
    chunk_overlap: Annotated[int | None, Form(ge=0, le=10_000)] = None,
    service: DocumentService = Depends(get_document_service),
) -> dict:
    try:
        return _public_document(service.reindex(document_id, chunk_size, chunk_overlap))
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/search", response_model=SearchResponse)
def search(
    request: SearchRequest, service: DocumentService = Depends(get_document_service)
) -> dict:
    return {"results": service.search(request.query, request.top_k)}
