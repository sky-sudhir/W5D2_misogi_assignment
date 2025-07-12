from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.schema import BaseRetriever, Document
from langchain.chains import RetrievalQA
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from config import config
from data_sources import stock_data_source, news_data_source
from vector_store import vector_store

class FinancialRetriever(BaseRetriever):
    """Custom retriever for financial data"""
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Retrieve relevant financial documents"""
        # Search vector store
        search_results = vector_store.search_all(query, limit=8)
        
        documents = []
        
        # Add news documents
        for result in search_results['news']:
            doc = Document(
                page_content=result['document'],
                metadata=result['metadata']
            )
            documents.append(doc)
        
        # Add stock data documents
        for result in search_results['stock_data']:
            doc = Document(
                page_content=result['document'],
                metadata=result['metadata']
            )
            documents.append(doc)
        
        return documents
    
    async def aget_relevant_documents(self, query: str) -> List[Document]:
        """Async version of get_relevant_documents"""
        return self.get_relevant_documents(query)

class StockMarketAgent:
    """Stock market analysis agent using RAG"""
    
    def __init__(self):
        # Initialize Groq LLM
        self.llm = ChatGroq(
            groq_api_key=config.GROQ_API_KEY,
            model_name="mixtral-8x7b-32768",
            temperature=0.1
        )
        
        # Initialize retriever
        self.retriever = FinancialRetriever()
        
        # Create tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        
        def get_stock_price(symbol: str) -> str:
            """Get current stock price and basic info"""
            try:
                data = stock_data_source.get_stock_price(symbol.upper())
                if data:
                    return json.dumps(data, indent=2)
                else:
                    return f"Could not retrieve data for {symbol}"
            except Exception as e:
                return f"Error retrieving stock data: {str(e)}"
        
        def get_company_news(company: str) -> str:
            """Get recent news about a specific company"""
            try:
                news = news_data_source.get_company_news(company, limit=5)
                if news:
                    return json.dumps(news[:3], indent=2)  # Return top 3 articles
                else:
                    return f"No recent news found for {company}"
            except Exception as e:
                return f"Error retrieving news: {str(e)}"
        
        def get_market_news() -> str:
            """Get general market news"""
            try:
                news = news_data_source.get_financial_news(limit=5)
                if news:
                    return json.dumps(news[:3], indent=2)
                else:
                    return "No recent market news available"
            except Exception as e:
                return f"Error retrieving market news: {str(e)}"
        
        def search_financial_data(query: str) -> str:
            """Search through stored financial data and news"""
            try:
                results = vector_store.search_all(query, limit=5)
                formatted_results = []
                
                for news_result in results['news']:
                    formatted_results.append({
                        'type': 'news',
                        'content': news_result['document'],
                        'metadata': news_result['metadata']
                    })
                
                for stock_result in results['stock_data']:
                    formatted_results.append({
                        'type': 'stock_data',
                        'content': stock_result['document'],
                        'metadata': stock_result['metadata']
                    })
                
                return json.dumps(formatted_results, indent=2)
            except Exception as e:
                return f"Error searching financial data: {str(e)}"
        
        return [
            Tool(
                name="get_stock_price",
                description="Get current stock price, change, volume, and basic metrics for a given stock symbol",
                func=get_stock_price
            ),
            Tool(
                name="get_company_news",
                description="Get recent news articles about a specific company",
                func=get_company_news
            ),
            Tool(
                name="get_market_news",
                description="Get general financial market news and headlines",
                func=get_market_news
            ),
            Tool(
                name="search_financial_data",
                description="Search through stored financial data, news, and historical information",
                func=search_financial_data
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the ReAct agent"""
        
        prompt = PromptTemplate.from_template("""
You are a professional financial advisor and stock market analyst. You help users make informed investment decisions by analyzing stock data, news, and market trends.

Your capabilities:
- Analyze stock prices and performance
- Provide market news and sentiment analysis
- Give investment recommendations (Buy/Hold/Sell)
- Explain market trends and company performance
- Search through financial data and news

Guidelines:
1. Always base your analysis on current data and news
2. Provide clear reasoning for your recommendations
3. Mention both opportunities and risks
4. Use specific numbers and facts when available
5. Be honest about limitations and uncertainties
6. Never guarantee returns or outcomes

Available tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
Thought: {agent_scratchpad}
""")
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    def analyze_stock(self, symbol: str) -> str:
        """Analyze a specific stock"""
        query = f"Analyze the stock {symbol}. Provide current price, recent news, and investment recommendation."
        return self.agent.invoke({"input": query})["output"]
    
    def get_market_summary(self) -> str:
        """Get general market summary"""
        query = "Provide a summary of current market conditions and trends based on recent news and data."
        return self.agent.invoke({"input": query})["output"]
    
    def answer_question(self, question: str) -> str:
        """Answer a general financial question"""
        return self.agent.invoke({"input": question})["output"]
    
    def get_investment_recommendation(self, symbol: str) -> str:
        """Get investment recommendation for a stock"""
        query = f"Should I buy, hold, or sell {symbol}? Provide a detailed analysis with reasoning."
        return self.agent.invoke({"input": query})["output"]

class DataIngestionService:
    """Service to regularly ingest and update financial data"""
    
    def __init__(self):
        self.last_news_update = 0
        self.last_stock_update = {}
    
    def update_news_data(self) -> None:
        """Update news data in vector store"""
        try:
            # Get latest financial news
            news = news_data_source.get_financial_news(limit=20)
            
            if news:
                # Add to vector store
                vector_store.add_news_articles(news)
                self.last_news_update = datetime.now().timestamp()
                print(f"Added {len(news)} news articles to vector store")
            
        except Exception as e:
            print(f"Error updating news data: {e}")
    
    def update_stock_data(self, symbols: List[str]) -> None:
        """Update stock data in vector store"""
        try:
            for symbol in symbols:
                # Get current stock data
                stock_info = stock_data_source.get_stock_price(symbol)
                
                if stock_info:
                    # Get historical data
                    historical_data = stock_data_source.get_historical_data(symbol)
                    
                    # Add to vector store
                    vector_store.add_stock_data(stock_info, historical_data)
                    self.last_stock_update[symbol] = datetime.now().timestamp()
                    print(f"Updated stock data for {symbol}")
                
        except Exception as e:
            print(f"Error updating stock data: {e}")
    
    def should_update_news(self) -> bool:
        """Check if news data should be updated"""
        current_time = datetime.now().timestamp()
        return current_time - self.last_news_update > config.NEWS_REFRESH_INTERVAL
    
    def should_update_stock(self, symbol: str) -> bool:
        """Check if stock data should be updated"""
        current_time = datetime.now().timestamp()
        last_update = self.last_stock_update.get(symbol, 0)
        return current_time - last_update > config.STOCK_REFRESH_INTERVAL

# Global instances
stock_agent = StockMarketAgent()
data_ingestion = DataIngestionService() 