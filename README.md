# Document Analysis Service - HNG Task 4

An AI-powered document analysis service that extracts text from PDF/DOCX files, summarizes content, detects document types, and extracts metadata using OpenRouter LLM with MinIO/S3 storage.

## Features
Document Upload: Accepts PDF and DOCX files (max 5MB)

Text Extraction: Extracts text using PyPDF2 and python-docx

AI Analysis: Sends text to OpenRouter LLM for summarization and metadata extraction

Storage: Uses MinIO (S3-compatible) for file storage with local fallback

REST API: FastAPI-based endpoints with OpenAPI documentation

Metadata Extraction: Identifies dates, sender, recipient, amounts, etc.

## Requirements
Python 3.8+

MinIO (or AWS S3)

OpenRouter API key (free tier available)

Installation
1. Clone and Setup
bash
# Clone repository
git clone <https://github.com/Ugoeze-hub/hng-7-be.git>

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
2. Environment Configuration
Create .env file:

env
# MinIO/S3 Configuration
S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_NAME=documents-bucket

# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
OPENROUTER_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free  # Free model, or any other

# Application Settings
APP_NAME="Document Analysis Service"
DEBUG=True
MAX_FILE_SIZE=5242880  # 5MB in bytes
3. MinIO Setup (Local Storage)
Option A: Using Docker (Recommended)
bash
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  -v minio-data:/data \
  --name minio \
  minio/minio server /data --console-address ":9001"
Option B: Using WSL/Ubuntu
bash
# Download MinIO binary
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
mkdir minio-data
./minio server minio-data --console-address ":9001"
Option C: Using Local Fallback (No Setup Needed)
The application automatically falls back to local file storage if MinIO is unavailable.

4. OpenRouter Setup
Sign up at https://openrouter.ai

Get API key from https://openrouter.ai/keys

Authorize models at https://openrouter.ai/models

Add your API key to .env file

Free Model Option: Use mistralai/mistral-7b-instruct:free for no-cost testing

Running the Application
bash
# Start MinIO (if using)
# Keep this running in separate terminal

# Start the application
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
The service will be available at: http://localhost:8000

API Endpoints
1. Upload Document
http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: <PDF or DOCX file>
Response:

json
{
  "id": "uuid",
  "filename": "document.pdf",
  "file_size": 12345,
  "upload_date": "2024-12-06T10:30:00Z",
  "s3_key": "documents/uuid/document.pdf",
  "extracted_text": "Full text content..."
}
2. Analyze Document
http
POST /api/v1/documents/{id}/analyze
Response:

json
{
  "summary": "Concise 2-3 sentence summary...",
  "document_type": "invoice",
  "metadata": {
    "date": "2024-12-06",
    "sender": "Company ABC",
    "recipient": "Client XYZ",
    "total_amount": "1500.00",
    "currency": "USD",
    "invoice_number": "INV-2024-001"
  },
  "confidence": 0.95
}
3. Get Document
http
GET /api/v1/documents/{id}
Response: Full document info including analysis results

4. List Documents
http
GET /api/v1/documents?skip=0&limit=10
5. Delete Document
http
DELETE /api/v1/documents/{id}
6. Health Check
http
GET /api/v1/health
Project Structure

 Testing
Using cURL
bash
# Upload document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@sample.pdf"

# Analyze document (replace {id} with actual ID)
curl -X POST http://localhost:8000/api/v1/documents/{id}/analyze

# Get document info
curl http://localhost:8000/api/v1/documents/{id}
Using Python
python
import requests

# Upload
with open('sample.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/api/v1/documents/upload', files=files)
    doc_id = response.json()['id']

# Analyze
analysis = requests.post(f'http://localhost:8000/api/v1/documents/{doc_id}/analyze')
print(analysis.json())


# License
This project was developed for HNG Backend Stage 7 Task 4.

# Acknowledgments
OpenRouter for LLM API access

MinIO for S3-compatible storage

FastAPI for the web framework

# Support
For issues and questions:

Review API documentation at http://localhost:8000/docs
Contact via email

Verify environment configuration

Status: Production Ready    
Last Updated: December 2025     
HNG Task: #7 - AI Document Summarization + Metadata Extraction