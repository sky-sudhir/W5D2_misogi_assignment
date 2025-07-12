import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from sentence_transformers import SentenceTransformer
from config import config

class FinancialVectorStore:
    """Vector store for financial documents using ChromaDB"""
    
    def __init__(self):
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=config.CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collections
        self.news_collection = self.client.get_or_create_collection(
            name="financial_news",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.stock_collection = self.client.get_or_create_collection(
            name="stock_data",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.reports_collection = self.client.get_or_create_collection(
            name="analyst_reports",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_news_articles(self, articles: List[Dict[str, Any]]) -> None:
        """Add news articles to the vector store"""
        if not articles:
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for article in articles:
            # Create document text
            doc_text = f"Title: {article['title']}\n"
            doc_text += f"Description: {article['description']}\n"
            if article.get('content'):
                doc_text += f"Content: {article['content']}\n"
            
            documents.append(doc_text)
            
            # Create metadata
            metadata = {
                'type': 'news',
                'title': article['title'],
                'source': article['source'],
                'published_at': article['published_at'],
                'sentiment': article['sentiment'],
                'url': article['url'],
                'added_at': datetime.now().isoformat()
            }
            metadatas.append(metadata)
            
            # Generate unique ID
            ids.append(str(uuid.uuid4()))
        
        # Add to collection
        self.news_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def add_stock_data(self, stock_info: Dict[str, Any], historical_data: Optional[Any] = None) -> None:
        """Add stock data to the vector store"""
        # Create document text for current stock info
        doc_text = f"Stock: {stock_info['symbol']}\n"
        doc_text += f"Current Price: ${stock_info['price']}\n"
        doc_text += f"Change: {stock_info['change']['change']} ({stock_info['change']['change_percent']}%)\n"
        doc_text += f"High: ${stock_info['high']}, Low: ${stock_info['low']}\n"
        doc_text += f"Volume: {stock_info['volume']}\n"
        doc_text += f"Timestamp: {stock_info['timestamp']}\n"
        
        # Add historical context if available
        if historical_data is not None and not historical_data.empty:
            recent_data = historical_data.tail(5)  # Last 5 days
            doc_text += "Recent Performance:\n"
            for date, row in recent_data.iterrows():
                doc_text += f"{date.strftime('%Y-%m-%d')}: Close ${row['4. close']:.2f}\n"
        
        metadata = {
            'type': 'stock_data',
            'symbol': stock_info['symbol'],
            'price': stock_info['price'],
            'change_percent': stock_info['change']['change_percent'],
            'timestamp': stock_info['timestamp'],
            'added_at': datetime.now().isoformat()
        }
        
        # Add to collection
        self.stock_collection.add(
            documents=[doc_text],
            metadatas=[metadata],
            ids=[f"stock_{stock_info['symbol']}_{int(datetime.now().timestamp())}"]
        )
    
    def search_news(self, query: str, limit: int = 5, sentiment_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for relevant news articles"""
        where_filter = {}
        if sentiment_filter:
            where_filter['sentiment'] = sentiment_filter
        
        results = self.news_collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter if where_filter else None
        )
        
        return self._format_search_results(results)
    
    def search_stock_data(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant stock data"""
        results = self.stock_collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        return self._format_search_results(results)
    
    def search_all(self, query: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all collections"""
        news_results = self.search_news(query, limit//2)
        stock_results = self.search_stock_data(query, limit//2)
        
        return {
            'news': news_results,
            'stock_data': stock_results
        }
    
    def get_recent_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent news articles"""
        results = self.news_collection.get(
            limit=limit,
            include=['documents', 'metadatas']
        )
        
        if not results['documents']:
            return []
        
        formatted_results = []
        for i, doc in enumerate(results['documents']):
            formatted_results.append({
                'document': doc,
                'metadata': results['metadatas'][i],
                'distance': 0.0  # No distance for direct retrieval
            })
        
        # Sort by added_at timestamp (most recent first)
        formatted_results.sort(
            key=lambda x: x['metadata'].get('added_at', ''),
            reverse=True
        )
        
        return formatted_results
    
    def _format_search_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Format search results into consistent structure"""
        if not results['documents'] or not results['documents'][0]:
            return []
        
        formatted_results = []
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        
        for i, doc in enumerate(documents):
            formatted_results.append({
                'document': doc,
                'metadata': metadatas[i],
                'distance': distances[i]
            })
        
        return formatted_results
    
    def clear_old_data(self, days_old: int = 7) -> None:
        """Clear old data from collections"""
        cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        # This is a simplified approach - in production, you'd want more sophisticated cleanup
        # ChromaDB doesn't have built-in TTL, so we'd need to implement custom cleanup logic
        pass
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about the collections"""
        return {
            'news_count': self.news_collection.count(),
            'stock_data_count': self.stock_collection.count(),
            'reports_count': self.reports_collection.count()
        }

# Global vector store instance
vector_store = FinancialVectorStore() 