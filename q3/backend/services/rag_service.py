import os
from typing import List, Dict, Any, Optional
import logging
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from models.schemas import DocumentChunk, RAGResponse

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.persist_directory = "chroma_db"
        self.collection_name = "code_tutor_docs"
        
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize ChromaDB
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        logger.info("RAG service initialized with ChromaDB")
    
    async def add_documents(self, document_chunks: List[DocumentChunk]) -> None:
        """Add document chunks to the vector store"""
        try:
            # Convert DocumentChunk objects to LangChain Document objects
            documents = []
            for chunk in document_chunks:
                doc = Document(
                    page_content=chunk.content,
                    metadata=chunk.metadata
                )
                documents.append(doc)
            
            # Add documents to vector store
            self.vector_store.add_documents(documents)
            
            # Persist the vector store
            self.vector_store.persist()
            
            logger.info(f"Added {len(document_chunks)} document chunks to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    async def search_similar_documents(
        self, 
        query: str, 
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents in the vector store"""
        try:
            # Perform similarity search
            if filter_metadata:
                results = self.vector_store.similarity_search(
                    query, 
                    k=k, 
                    filter=filter_metadata
                )
            else:
                results = self.vector_store.similarity_search(query, k=k)
            
            logger.info(f"Found {len(results)} similar documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            return []
    
    async def search_with_scores(
        self, 
        query: str, 
        k: int = 5,
        score_threshold: float = 0.5
    ) -> List[tuple]:
        """Search for similar documents with similarity scores"""
        try:
            # Perform similarity search with scores
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Filter by score threshold
            filtered_results = [
                (doc, score) for doc, score in results 
                if score >= score_threshold
            ]
            
            logger.info(f"Found {len(filtered_results)} documents above threshold {score_threshold}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching with scores: {str(e)}")
            return []
    
    async def get_relevant_context(
        self, 
        code: str, 
        language: str, 
        error_message: Optional[str] = None,
        k: int = 3
    ) -> List[Document]:
        """Get relevant context for code explanation"""
        try:
            # Build search query
            query_parts = [f"{language} code"]
            
            if error_message:
                query_parts.append(f"error: {error_message}")
            
            # Add code snippet (truncated for search)
            code_snippet = code[:200] if len(code) > 200 else code
            query_parts.append(code_snippet)
            
            query = " ".join(query_parts)
            
            # Search for relevant documents
            relevant_docs = await self.search_similar_documents(query, k=k)
            
            return relevant_docs
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        try:
            collection = self.vector_store._collection
            count = collection.count()
            
            return {
                "document_count": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}
    
    async def delete_documents(self, filter_metadata: Dict[str, Any]) -> bool:
        """Delete documents from vector store based on metadata filter"""
        try:
            # ChromaDB delete functionality
            collection = self.vector_store._collection
            
            # Get document IDs that match the filter
            results = collection.get(where=filter_metadata)
            
            if results and results['ids']:
                collection.delete(ids=results['ids'])
                self.vector_store.persist()
                logger.info(f"Deleted {len(results['ids'])} documents")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            return False 