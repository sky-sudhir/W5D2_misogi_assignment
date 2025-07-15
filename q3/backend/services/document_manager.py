import os
import uuid
from typing import List, Dict, Any
from fastapi import UploadFile
import aiofiles
import logging

from langchain.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredHTMLLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from models.schemas import DocumentChunk

logger = logging.getLogger(__name__)

class DocumentManager:
    def __init__(self):
        self.upload_dir = "uploads"
        self.supported_extensions = {
            '.txt': TextLoader,
            '.md': UnstructuredMarkdownLoader,
            '.pdf': PyPDFLoader,
            '.docx': UnstructuredWordDocumentLoader,
            '.html': UnstructuredHTMLLoader
        }
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> str:
        """Save uploaded file to disk"""
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1].lower()
        file_path = os.path.join(self.upload_dir, f"{file_id}{file_extension}")
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"Saved uploaded file: {file.filename} -> {file_path}")
        return file_path
    
    async def process_document(self, file_path: str) -> List[DocumentChunk]:
        """Process document using LangChain loaders and split into chunks"""
        try:
            # Get file extension
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Check if file type is supported
            if file_extension not in self.supported_extensions:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Load document using appropriate loader
            loader_class = self.supported_extensions[file_extension]
            loader = loader_class(file_path)
            documents = loader.load()
            
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Convert to DocumentChunk objects
            document_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{os.path.basename(file_path)}_{i}"
                document_chunk = DocumentChunk(
                    content=chunk.page_content,
                    metadata={
                        **chunk.metadata,
                        "source": file_path,
                        "chunk_index": i,
                        "chunk_id": chunk_id
                    },
                    chunk_id=chunk_id
                )
                document_chunks.append(document_chunk)
            
            logger.info(f"Processed document {file_path} into {len(document_chunks)} chunks")
            return document_chunks
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise
    
    def get_document_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata for a document"""
        return {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "file_extension": os.path.splitext(file_path)[1].lower()
        }
    
    async def delete_document(self, file_path: str) -> bool:
        """Delete a document file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted document: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document {file_path}: {str(e)}")
            return False 