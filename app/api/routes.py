from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from typing import List
from app.models.schemas import DocumentInfo, AnalysisResult, DocumentListResponse
from app.services.storage import StorageService
from app.services.text_extraction import TextExtractionService
from app.services.llm_analysis import LLMAnalysisService
from app.database.repository import DocumentRepository
from app.config import get_settings
import os

router = APIRouter()

# Service instances
storage_service = StorageService()
text_service = TextExtractionService()
llm_service = LLMAnalysisService()
doc_repository = DocumentRepository()

def get_settings_dep():
    return get_settings()

@router.post("/documents/upload", response_model=DocumentInfo, 
             status_code=status.HTTP_201_CREATED, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    settings: dict = Depends(get_settings_dep)
):
    """Upload a PDF document for processing."""
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {', '.join(settings.allowed_extensions)} files are supported"
        )
    
    # Read and validate file size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {settings.max_file_size / (1024*1024)}MB limit"
        )
    
    # Extract text
    extracted_text = text_service.extract_from_pdf(file_content)
    
    # Generate S3 key and upload
    doc_id = str(uuid.uuid4())
    s3_key = f"documents/{doc_id}/{file.filename}"
    storage_service.upload_file(file_content, s3_key)
    
    # Save to database
    doc_info = doc_repository.create_document(
        filename=file.filename,
        file_size=file_size,
        s3_key=s3_key,
        extracted_text=extracted_text
    )
    
    return doc_info

@router.post("/documents/{id}/analyze", response_model=AnalysisResult, 
             tags=["Documents"])
async def analyze_document(id: str):
    """Analyze a document using LLM."""
    
    doc = doc_repository.get_document(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not doc.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No text available for analysis"
        )
    
    # Analyze with LLM
    analysis = await llm_service.analyze_text(doc.extracted_text)
    
    # Update database
    doc_repository.update_analysis(id, analysis)
    
    return analysis

@router.get("/documents/{id}", response_model=DocumentInfo, tags=["Documents"])
async def get_document(id: str):
    """Get document information including analysis results."""
    
    doc = doc_repository.get_document(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return doc

@router.get("/documents", response_model=DocumentListResponse, tags=["Documents"])
async def list_documents(skip: int = 0, limit: int = 10):
    """List all uploaded documents with pagination."""
    
    documents, total = doc_repository.list_documents(skip, limit)
    
    return DocumentListResponse(
        total=total,
        skip=skip,
        limit=limit,
        documents=documents
    )

@router.delete("/documents/{id}", status_code=status.HTTP_204_NO_CONTENT, 
               tags=["Documents"])
async def delete_document(id: str):
    """Delete a document and its associated data."""
    
    doc = doc_repository.get_document(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from S3
    storage_service.delete_file(doc.s3_key)
    
    # Delete from database
    doc_repository.delete_document(id)
    
    return None

@router.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "documents_count": doc_repository.count()
    }
