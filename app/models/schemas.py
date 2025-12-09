from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

class DocumentType(str, Enum):
    INVOICE = "invoice"
    CV = "cv"
    REPORT = "report"
    LETTER = "letter"
    CONTRACT = "contract"
    RECEIPT = "receipt"
    OTHER = "other"


class AnalysisResult(BaseModel):
    summary: str
    document_type: DocumentType
    metadata: Optional[Dict[str, Any]] = None

class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_size: int
    upload_date: str
    s3_key: str
    extracted_text: Optional[str] = None
    analysis: Optional[AnalysisResult] = None

class ErrorResponse(BaseModel):
    error: str = "Failed"
    detail: Optional[str] = None

class DocumentListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    documents: list[DocumentInfo]