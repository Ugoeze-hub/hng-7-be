from typing import Dict, List, Optional
import uuid
from datetime import datetime
from app.models.schemas import DocumentInfo, AnalysisResult

class DocumentRepository:
    """In-memory document repository. Replace with actual DB in production."""
    
    def __init__(self):
        self._storage: Dict[str, dict] = {}
    
    def create_document(self, filename: str, file_size: int, s3_key: str, 
                       extracted_text: str) -> DocumentInfo:
        """Create a new document record."""
        doc_id = str(uuid.uuid4())
        
        doc_data = {
            "id": doc_id,
            "filename": filename,
            "file_size": file_size,
            "upload_date": datetime.utcnow().isoformat(),
            "s3_key": s3_key,
            "extracted_text": extracted_text,
            "analysis": None
        }
        
        self._storage[doc_id] = doc_data
        return DocumentInfo(**doc_data)
    
    def get_document(self, doc_id: str) -> Optional[DocumentInfo]:
        """Retrieve a document by ID."""
        doc = self._storage.get(doc_id)
        if not doc:
            return None
        
        # Convert analysis dict to model if present
        if doc["analysis"]:
            doc = doc.copy()
            doc["analysis"] = AnalysisResult(**doc["analysis"])
        
        return DocumentInfo(**doc)
    
    def update_analysis(self, doc_id: str, analysis: AnalysisResult) -> bool:
        """Update document with analysis results."""
        if doc_id not in self._storage:
            return False
        
        self._storage[doc_id]["analysis"] = analysis.dict()
        return True
    
    def list_documents(self, skip: int = 0, limit: int = 10) -> tuple[List[DocumentInfo], int]:
        """List documents with pagination."""
        docs = list(self._storage.values())
        total = len(docs)
        paginated = docs[skip:skip + limit]
        
        # Convert analysis dicts to models
        result = []
        for doc in paginated:
            doc = doc.copy()
            if doc["analysis"]:
                doc["analysis"] = AnalysisResult(**doc["analysis"])
            result.append(DocumentInfo(**doc))
        
        return result, total
    
    def delete_document(self, doc_id: str) -> Optional[dict]:
        """Delete a document."""
        return self._storage.pop(doc_id, None)
    
    def count(self) -> int:
        """Get total document count."""
        return len(self._storage)