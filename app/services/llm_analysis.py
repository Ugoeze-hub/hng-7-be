import httpx
import json
from fastapi import HTTPException, status
from app.models.schemas import AnalysisResult, DocumentMetadata
from app.config import get_settings
import logging

logger = logging.getLogger("__name__")

class LLMAnalysisService:
    def __init__(self):
        self.settings = get_settings()
    
    def _build_prompt(self, text: str) -> str:
        """Build the analysis prompt."""
        truncated_text = text[:self.settings.text_truncate_length]
        
        return f"""Analyze the following document and provide:
1. A concise summary (2-3 sentences)
2. Document type (invoice, cv, report, letter, contract, receipt, or other)
3. Extracted metadata including:
   - date (if present)
   - sender/from (if present)
   - recipient/to (if present)
   - total_amount (if present, numeric value only)
   - currency (if present)
   - invoice_number (if present)
   - company (if present)
   - email (if present)
   - phone (if present)

Respond ONLY with valid JSON in this exact format:
{{
  "summary": "brief summary here",
  "document_type": "one of: invoice, cv, report, letter, contract, receipt, other",
  "metadata": {{
    "date": "extracted date or null",
    "sender": "sender name or null",
    "recipient": "recipient name or null",
    "total_amount": "numeric amount or null",
    "currency": "currency code or null",
    "invoice_number": "invoice number or null",
    "company": "company name or null",
    "email": "email address or null",
    "phone": "phone number or null"
  }},
  "confidence": 0.95
}}

Document text:
{truncated_text}"""
    
    def _parse_llm_response(self, content: str) -> dict:
        """Parse LLM JSON response."""
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse LLM response: {str(e)}"
            )
    
    async def analyze_text(self, text: str) -> AnalysisResult:
        """Analyze document text using LLM."""
        prompt = self._build_prompt(text)
        
        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout) as client:
                headers={
                    "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": self.settings.app_name
                }
                
                response = await client.post(
                    self.settings.openrouter_url,
                    headers=headers,
                    json={
                    "model": self.settings.openrouter_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.settings.llm_temperature,
                    "max_tokens": self.settings.llm_max_tokens
                }   
                )  

                if response.status_code == 401:
                    logger.warning("API key rejected") 
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"LLM API error: {response.text}"
                    )   
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"LLM API error: {response.text}"
                    )
                
                result = response.json()
                if "choices" not in result or not result["choices"]:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="LLM returned empty response"
                    )
                content = result["choices"][0]["message"]["content"]
                parsed = self._parse_llm_response(content)
                
                return AnalysisResult(
                    summary=parsed["summary"],
                    document_type=parsed["document_type"],
                    metadata=DocumentMetadata(**parsed["metadata"]),
                    confidence=parsed.get("confidence", 0.9)
                )
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="LLM API request timed out"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LLM analysis failed: {str(e)}"
            )
