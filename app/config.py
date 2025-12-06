from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Document Analysis Service"
    debug: bool = False
    
    s3_bucket: str = "documents-bucket"
    s3_endpoint: str = "http://localhost:9000"
    aws_access_key: str = "minioadmin"
    aws_secret_key: str = "minioadmin"
  
    openrouter_api_key: str
    openrouter_url: str 
    openrouter_model: str
    
 
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    allowed_extensions: list = [".pdf"]

    llm_timeout: int = 60
    llm_max_tokens: int = 1000
    llm_temperature: float = 0.3
    text_truncate_length: int = 4000
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()