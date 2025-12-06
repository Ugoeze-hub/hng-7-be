from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Document Analysis Service"
    debug: bool = False
    
    s3_bucket: str 
    s3_endpoint: str
    aws_access_key: str 
    aws_secret_key: str 
  
    openrouter_api_key: str
    openrouter_url: str 
    openrouter_model: str
    
 
    max_file_size: int
    allowed_extensions: list 

    llm_timeout: int 
    llm_max_tokens: int 
    llm_temperature: float 
    text_truncate_length: int 
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()