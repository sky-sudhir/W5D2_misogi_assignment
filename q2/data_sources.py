import requests
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
from alpha_vantage.timeseries import TimeSeries
from newsapi import NewsApiClient
from config import config

class StockDataSource:
    """Alpha Vantage stock data integration"""
    
    def __init__(self):
        if not config.ALPHA_VANTAGE_API_KEY:
            raise ValueError("Alpha Vantage API key is required")
        self.ts = TimeSeries(key=config.ALPHA_VANTAGE_API_KEY, output_format='pandas')
        self.cache = {}
        self.cache_timestamps = {}
    
    def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock price with caching"""
        cache_key = f"price_{symbol}"
        current_time = time.time()
        
        # Check cache (refresh every 30 seconds)
        if (cache_key in self.cache and 
            current_time - self.cache_timestamps.get(cache_key, 0) < config.STOCK_REFRESH_INTERVAL):
            return self.cache[cache_key]
        
        try:
            # Get intraday data (1min intervals)
            data, meta_data = self.ts.get_intraday(symbol=symbol, interval='1min', outputsize='compact')
            
            if data.empty:
                return None
            
            # Get latest price
            latest_time = data.index[-1]
            latest_data = data.iloc[-1]
            
            price_info = {
                'symbol': symbol,
                'price': float(latest_data['4. close']),
                'high': float(latest_data['2. high']),
                'low': float(latest_data['3. low']),
                'volume': int(latest_data['5. volume']),
                'timestamp': latest_time.strftime('%Y-%m-%d %H:%M:%S'),
                'change': self._calculate_change(data)
            }
            
            # Cache the result
            self.cache[cache_key] = price_info
            self.cache_timestamps[cache_key] = current_time
            
            return price_info
            
        except Exception as e:
            print(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = '1year') -> Optional[pd.DataFrame]:
        """Get historical stock data"""
        try:
            if period == '1year':
                data, meta_data = self.ts.get_daily(symbol=symbol, outputsize='full')
                # Get last year of data
                one_year_ago = datetime.now() - timedelta(days=365)
                data = data[data.index >= one_year_ago]
            else:
                data, meta_data = self.ts.get_daily(symbol=symbol, outputsize='compact')
            
            return data
            
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def _calculate_change(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate price change and percentage change"""
        if len(data) < 2:
            return {'change': 0.0, 'change_percent': 0.0}
        
        current_price = float(data.iloc[-1]['4. close'])
        previous_price = float(data.iloc[-2]['4. close'])
        
        change = current_price - previous_price
        change_percent = (change / previous_price) * 100 if previous_price != 0 else 0.0
        
        return {
            'change': round(change, 2),
            'change_percent': round(change_percent, 2)
        }

class NewsDataSource:
    """NewsAPI integration for financial news"""
    
    def __init__(self):
        if not config.NEWS_API_KEY:
            raise ValueError("News API key is required")
        self.newsapi = NewsApiClient(api_key=config.NEWS_API_KEY)
        self.cache = {}
        self.cache_timestamp = 0
    
    def get_financial_news(self, query: str = "stock market", limit: int = 20) -> List[Dict[str, Any]]:
        """Get financial news with caching"""
        current_time = time.time()
        
        # Check cache (refresh every hour)
        if (self.cache and 
            current_time - self.cache_timestamp < config.NEWS_REFRESH_INTERVAL):
            return self.cache.get('news', [])
        
        try:
            # Get news from multiple financial sources
            financial_sources = [
                'bloomberg', 'reuters', 'cnbc', 'financial-times', 
                'the-wall-street-journal', 'marketwatch'
            ]
            
            all_articles = []
            
            # Get top business headlines
            headlines = self.newsapi.get_top_headlines(
                category='business',
                language='en',
                page_size=limit
            )
            
            if headlines['status'] == 'ok':
                all_articles.extend(headlines['articles'])
            
            # Get specific financial news
            everything = self.newsapi.get_everything(
                q=query,
                sources=','.join(financial_sources),
                language='en',
                sort_by='publishedAt',
                page_size=limit
            )
            
            if everything['status'] == 'ok':
                all_articles.extend(everything['articles'])
            
            # Process and deduplicate articles
            processed_articles = self._process_articles(all_articles)
            
            # Cache the results
            self.cache['news'] = processed_articles
            self.cache_timestamp = current_time
            
            return processed_articles
            
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
    
    def get_company_news(self, company: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get news specific to a company"""
        try:
            news = self.newsapi.get_everything(
                q=company,
                language='en',
                sort_by='publishedAt',
                page_size=limit
            )
            
            if news['status'] == 'ok':
                return self._process_articles(news['articles'])
            
            return []
            
        except Exception as e:
            print(f"Error fetching company news for {company}: {e}")
            return []
    
    def _process_articles(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """Process and clean news articles"""
        processed = []
        seen_titles = set()
        
        for article in articles:
            # Skip articles without title or description
            if not article.get('title') or not article.get('description'):
                continue
            
            # Deduplicate by title
            if article['title'] in seen_titles:
                continue
            seen_titles.add(article['title'])
            
            processed_article = {
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'source': article['source']['name'],
                'published_at': article['publishedAt'],
                'content': article.get('content', ''),
                'sentiment': self._analyze_sentiment(article['title'] + ' ' + article['description'])
            }
            
            processed.append(processed_article)
        
        return processed[:20]  # Limit to 20 articles
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis based on keywords"""
        positive_keywords = ['gain', 'rise', 'up', 'bull', 'positive', 'growth', 'profit', 'surge']
        negative_keywords = ['loss', 'fall', 'down', 'bear', 'negative', 'decline', 'drop', 'crash']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

# Global instances
stock_data_source = StockDataSource()
news_data_source = NewsDataSource() 