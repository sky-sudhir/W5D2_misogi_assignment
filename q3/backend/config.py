import os
from typing import Optional

class Config:
    # Groq API Configuration
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    
    # E2B Configuration
    E2B_API_KEY: Optional[str] = os.getenv("E2B_API_KEY")
    
    # Application Configuration
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database Configuration
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    
    # File Upload Configuration
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    # CORS Configuration
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    @classmethod
    def validate(cls):
        """Validate required environment variables"""
        required_vars = ["GROQ_API_KEY", "E2B_API_KEY"]
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Create global config instance
config = Config() 