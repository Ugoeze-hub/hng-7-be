import re
import httpx
import json
from fastapi import HTTPException, status
from app.models.schemas import AnalysisResult, DocumentType
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

class LLMAnalysisService:
    def __init__(self):
        self.settings = get_settings()
    
    def _build_prompt(self, text: str) -> str:
        """Build the analysis prompt."""
        truncated_text = text[:self.settings.text_truncate_length]
        
        return f"""DOCUMENT:
{truncated_text}

IMPORTANT: Return ONLY raw JSON, no markdown code blocks, no backticks, no extra text.

Return this JSON structure:
{{
  "summary": "3-4 sentence summary here",
  "document_type": "one of: invoice, cv, report, letter, contract, receipt, other",
  "metadata": {{
    "key1": "value1",
    "key2": "value2"
  }}
}}

Extract any relevant metadata fields such as:
- date, invoice_number, receipt_number
- from, to, sender, recipient, company
- total_amount, currency, payment_method
- email, phone, address
- Any other relevant fields

REMEMBER: Return ONLY the JSON object, nothing else."""
    
    def _parse_llm_response(self, content: str) -> dict:
        """Parse LLM JSON response."""

        if not content or not content.strip():
            logger.error("Received empty response from LLM")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM returned empty response"
            )
        
        logger.info(f"Raw response preview: {content[:200]}...")

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Direct JSON parse failed: {str(e)}")
            
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError as e2:
                    logger.error(f"Regex extraction failed: {str(e2)}")
                    logger.error(f"Content that failed: {content[:500]}")
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
                logger.info(f"Sending request to OpenRouter...")
                logger.info(f"Model: {self.settings.openrouter_model}")
                logger.info(f"Prompt length: {len(prompt)} chars")
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

                logger.info(f"Response status: {response.status_code}")

                if response.status_code == 401:
                    logger.warning("API key rejected") 
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"LLM API error: {response.text}"
                    )   
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"OpenRouter API error: {error_detail}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"LLM API error: {error_detail}"
                    )
                
                result = response.json()
                logger.info(f"Parsed JSON response keys: {list(result.keys())}")
                
                logger.debug(f"Full result: {json.dumps(result, indent=2)}")

                if "error" in result:
                    error_msg = result["error"].get("message", "Unknown error")
                    logger.error(f"OpenRouter returned error: {error_msg}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"OpenRouter error: {error_msg}"
                    )

                if "choices" not in result or not result["choices"]:
                    logger.error("No choices in response")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="LLM returned empty response"
                    )
                content = result["choices"][0]["message"]["content"]
                logger.debug(f"LLM content preview: {content[:300]}")

                parsed = self._parse_llm_response(content)

                required_fields = ["summary", "document_type", "metadata"]
                for field in required_fields:
                    if field not in parsed:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"LLM response missing required field: {field}"
                        )
                
                doc_type_str = str(parsed["document_type"]).lower().strip()
                try:
                    document_type = DocumentType(doc_type_str)
                except ValueError:
                    document_type = DocumentType.OTHER
                    logger.warning(f"Unknown document type '{doc_type_str}', using 'other'")
                
                metadata_dict = parsed.get("metadata", {})
                cleaned_metadata = None
                
                if metadata_dict and isinstance(metadata_dict, dict):
                    cleaned_metadata = {}
                    for key, value in metadata_dict.items():
                        if value is not None:
                            cleaned_metadata[str(key)] = value
                    
                    if not cleaned_metadata:
                        cleaned_metadata = None
                
                logger.info(f"Analysis complete. Type: {document_type}, Metadata fields: {list(cleaned_metadata.keys()) if cleaned_metadata else 'none'}")
                
                return AnalysisResult(
                    summary=parsed["summary"],
                    document_type=document_type,
                    metadata=cleaned_metadata
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
