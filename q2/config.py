import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the stock market chat agent"""
    
    # API Keys
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    NEWS_API_KEY: Optional[str] = os.getenv("NEWS_API_KEY")
    
    # LangSmith Configuration
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    LANGCHAIN_API_KEY: Optional[str] = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "stock-market-agent")
    
    # Application Settings
    NEWS_REFRESH_INTERVAL: int = int(os.getenv("NEWS_REFRESH_INTERVAL", "3600"))
    STOCK_REFRESH_INTERVAL: int = int(os.getenv("STOCK_REFRESH_INTERVAL", "30"))
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "10"))
    
    # Vector Database
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    
    @classmethod
    def validate_required_keys(cls) -> None:
        """Validate that required API keys are present"""
        required_keys = ["GROQ_API_KEY", "ALPHA_VANTAGE_API_KEY", "NEWS_API_KEY"]
        missing_keys = [key for key in required_keys if not getattr(cls, key)]
        
        if missing_keys:
            raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")

# Global config instance
config = Config() 