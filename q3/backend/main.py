import asyncio
import os
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv
import json
import logging

from services.code_executor import CodeExecutor
from services.rag_service import RAGService
from services.document_manager import DocumentManager
from services.langgraph_agent import CodeTutorAgent
from models.schemas import CodeExecutionRequest, ExecutionResult

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Smart Code Tutor API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
code_executor = CodeExecutor()
document_manager = DocumentManager()
rag_service = RAGService()
code_tutor_agent = CodeTutorAgent()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Smart Code Tutor API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": {
        "code_executor": "ready",
        "rag_service": "ready",
        "document_manager": "ready"
    }}

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document for RAG"""
    try:
        # Save uploaded file
        file_path = await document_manager.save_uploaded_file(file)
        
        # Process and embed document
        chunks = await document_manager.process_document(file_path)
        await rag_service.add_documents(chunks)
        
        return JSONResponse({
            "message": f"Document {file.filename} uploaded and processed successfully",
            "chunks_created": len(chunks)
        })
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "run_code":
                await handle_code_execution(client_id, message["payload"])
            elif message["type"] == "ping":
                await manager.send_message(client_id, {"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
        await manager.send_message(client_id, {
            "type": "error",
            "message": str(e)
        })

async def handle_code_execution(client_id: str, payload: dict):
    """Handle code execution and AI explanation"""
    try:
        code = payload["code"]
        language = payload["language"]
        
        # Send status update
        await manager.send_message(client_id, {
            "type": "status",
            "message": "Starting code execution..."
        })
        
        # Execute code with streaming output
        execution_result = await code_executor.execute_code(
            code, language, 
            output_callback=lambda output: asyncio.create_task(
                manager.send_message(client_id, {
                    "type": "execution_output",
                    "data": output
                })
            )
        )
        
        # Send execution completion
        await manager.send_message(client_id, {
            "type": "execution_complete",
            "result": execution_result.dict()
        })
        
        # Generate AI explanation using LangGraph
        await manager.send_message(client_id, {
            "type": "status",
            "message": "Generating AI explanation..."
        })
        
        # Stream AI explanation
        async for explanation_chunk in code_tutor_agent.generate_explanation(
            code, language, execution_result
        ):
            await manager.send_message(client_id, {
                "type": "rag_explanation",
                "data": explanation_chunk
            })
        
        # Send completion status
        await manager.send_message(client_id, {
            "type": "status",
            "message": "Ready"
        })
        
    except Exception as e:
        logger.error(f"Error in code execution for client {client_id}: {str(e)}")
        await manager.send_message(client_id, {
            "type": "execution_error",
            "message": str(e)
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 