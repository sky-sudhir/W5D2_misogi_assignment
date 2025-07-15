from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"

class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"

class CodeExecutionRequest(BaseModel):
    code: str
    language: Language

class ExecutionResult(BaseModel):
    status: ExecutionStatus
    stdout: str
    stderr: str
    execution_time: float
    exit_code: Optional[int] = None
    error_message: Optional[str] = None

class DocumentChunk(BaseModel):
    content: str
    metadata: Dict[str, Any]
    chunk_id: str

class RAGResponse(BaseModel):
    explanation: str
    sources: List[str]
    confidence: float

class WebSocketMessage(BaseModel):
    type: str
    payload: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None 