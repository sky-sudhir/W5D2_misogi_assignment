# 📈 AI Stock Market Chat Agent

A real-time stock market chat application powered by Groq LLMs, Alpha Vantage stock data, and NewsAPI. Users can interact with the AI via a Streamlit interface to get real-time stock updates, news, and personalized investment recommendations.

## 🚀 Features

- **Interactive Chat Interface**: Streamlit-based chat UI with streaming responses
- **Real-time Stock Data**: Live stock prices, historical data, and market metrics
- **Financial News Integration**: Latest market news with sentiment analysis
- **AI-Powered Recommendations**: Buy/Hold/Sell decisions based on data analysis
- **RAG (Retrieval-Augmented Generation)**: Enhanced responses using vector search
- **Rate Limiting**: Built-in protection against API abuse
- **Monitoring & Analytics**: LangSmith integration for performance tracking

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Backend | Python, LangChain |
| LLM | Groq (Mixtral-8x7B) |
| Vector Store | ChromaDB |
| Embeddings | SentenceTransformers |
| Stock Data | Alpha Vantage API |
| News Data | NewsAPI |
| Rate Limiting | SlowAPI |
| Monitoring | LangSmith |

## 📋 Prerequisites

- Python 3.8+
- API Keys for:
  - [Groq](https://groq.com/) - For LLM inference
  - [Alpha Vantage](https://www.alphavantage.co/) - For stock data
  - [NewsAPI](https://newsapi.org/) - For financial news
  - [LangSmith](https://smith.langchain.com/) - For monitoring (optional)

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd stock-market-chat-agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` with your API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
   NEWS_API_KEY=your_news_api_key_here
   
   # Optional: LangSmith monitoring
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your_langsmith_api_key_here
   LANGCHAIN_PROJECT=stock-market-agent
   ```

## 🚀 Usage

1. **Start the application**:
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Open your browser** and navigate to `http://localhost:8501`

3. **Start chatting** with the AI about stocks, markets, and investments!

## 💬 Example Queries

- "What's the current price of Apple stock?"
- "Should I invest in Tesla right now?"
- "What are the latest market trends?"
- "Compare Microsoft and Google stocks"
- "Give me news about Amazon"
- "Is it a good time to buy Netflix?"

## 🏗️ Architecture

```
User (Streamlit Chat)
        ↓
Rate Limiter → Agent (LangChain + Groq)
        ↓              ↑
    Response    ← RAG System ← Vector Store (ChromaDB)
                      ↑              ↑
                 Data Sources → News + Stock Data
                      ↑
                 Monitoring (LangSmith)
```

## 📁 Project Structure

```
├── streamlit_app.py      # Main Streamlit application
├── config.py             # Configuration management
├── data_sources.py       # Stock & news data integration
├── vector_store.py       # ChromaDB vector store
├── rag_agent.py          # LangChain RAG agent
├── rate_limiter.py       # Rate limiting functionality
├── monitoring.py         # LangSmith monitoring
├── requirements.txt      # Python dependencies
├── env.example          # Environment variables template
└── README.md            # This file
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM | Yes |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | Yes |
| `NEWS_API_KEY` | NewsAPI key | Yes |
| `LANGCHAIN_API_KEY` | LangSmith API key | No |
| `NEWS_REFRESH_INTERVAL` | News refresh interval (seconds) | No |
| `STOCK_REFRESH_INTERVAL` | Stock refresh interval (seconds) | No |
| `MAX_REQUESTS_PER_MINUTE` | Rate limit per minute | No |

### Default Settings

- News refresh: Every 1 hour
- Stock refresh: Every 30 seconds
- Rate limit: 10 requests per minute
- Vector store: Local ChromaDB

## 🔒 Rate Limiting

The application includes built-in rate limiting to prevent API abuse:

- **Streamlit Interface**: 10 requests per minute per session
- **Visual Feedback**: Progress bar showing remaining requests
- **Graceful Degradation**: Clear error messages when limits are exceeded

## 📊 Monitoring

LangSmith integration provides:

- **Request Tracking**: All agent interactions logged
- **Performance Metrics**: Response times and success rates
- **Tool Usage Analytics**: Which tools are used most frequently
- **Error Monitoring**: Failed requests and error patterns

## 🛡️ Security Considerations

- API keys stored in environment variables
- Rate limiting prevents abuse
- Input validation on all user inputs
- Error handling prevents information leakage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Ensure all required API keys are set in `.env`
   - Check API key validity and quotas

2. **Rate Limiting**:
   - Wait for the rate limit to reset
   - Consider upgrading API plans for higher limits

3. **ChromaDB Issues**:
   - Delete `./chroma_db` directory to reset vector store
   - Ensure sufficient disk space

4. **Streamlit Issues**:
   - Clear browser cache
   - Restart the Streamlit server

### Getting Help

- Check the console for error messages
- Review the LangSmith dashboard for detailed traces
- Open an issue on GitHub with error details

## 🚀 Future Enhancements

- [ ] Portfolio tracking and management
- [ ] Technical analysis indicators
- [ ] Multi-language support
- [ ] Mobile-responsive design
- [ ] Real-time price alerts
- [ ] Integration with more data sources
- [ ] Advanced charting capabilities

---

**Disclaimer**: This application is for educational and informational purposes only. It should not be considered as financial advice. Always consult with a qualified financial advisor before making investment decisions. 