from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class DocumentType(str, Enum):
    INVOICE = "invoice"
    CV = "cv"
    REPORT = "report"
    LETTER = "letter"
    CONTRACT = "contract"
    RECEIPT = "receipt"
    OTHER = "other"

class DocumentMetadata(BaseModel):
    date: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    total_amount: Optional[str] = None
    currency: Optional[str] = None
    invoice_number: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    additional_fields: Optional[Dict[str, Any]] = None

class AnalysisResult(BaseModel):
    summary: str
    document_type: DocumentType
    metadata: DocumentMetadata
    confidence: Optional[float] = None

class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_size: int
    upload_date: str
    s3_key: str
    extracted_text: Optional[str] = None
    analysis: Optional[AnalysisResult] = None

class DocumentListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    documents: list[DocumentInfo]