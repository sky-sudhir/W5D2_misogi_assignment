import streamlit as st
import time

from config import config
from rag_agent import stock_agent, data_ingestion
from vector_store import vector_store
from rate_limiter import check_rate_limit_streamlit, display_rate_limit_info

# Page configuration
st.set_page_config(
    page_title="📈 AI Stock Market Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1f4e79, #2d5aa0);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #2d5aa0;
    }
    
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #2d5aa0;
    }
    
    .assistant-message {
        background-color: #e8f4f8;
        border-left-color: #1f4e79;
    }
    
    .sidebar-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm your AI Stock Market Assistant. I can help you with:\n\n"
                          "• 📊 Stock price analysis and recommendations\n"
                          "• 📰 Latest financial news and market trends\n"
                          "• 💡 Investment insights and portfolio advice\n"
                          "• 🔍 Company research and analysis\n\n"
                          "What would you like to know about the stock market today?"
            }
        ]
    
    if "data_initialized" not in st.session_state:
        st.session_state.data_initialized = False
    
    if "popular_stocks" not in st.session_state:
        st.session_state.popular_stocks = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA"]

def initialize_data():
    """Initialize data sources and vector store"""
    if not st.session_state.data_initialized:
        with st.spinner("Initializing financial data..."):
            try:
                # Update news data
                data_ingestion.update_news_data()
                
                # Update stock data for popular stocks
                data_ingestion.update_stock_data(st.session_state.popular_stocks)
                
                st.session_state.data_initialized = True
                st.success("✅ Financial data initialized successfully!")
                
            except Exception as e:
                st.error(f"❌ Error initializing data: {str(e)}")
                st.info("💡 Please check your API keys in the configuration.")

def display_sidebar():
    """Display sidebar with market information and controls"""
    with st.sidebar:
        st.markdown("## 📊 Market Dashboard")
        
        # Vector store statistics
        try:
            stats = vector_store.get_collection_stats()
            st.markdown(f"""
            <div class="sidebar-info">
                <h4>📈 Data Status</h4>
                <p>📰 News Articles: {stats['news_count']}</p>
                <p>📊 Stock Records: {stats['stock_data_count']}</p>
                <p>📋 Reports: {stats['reports_count']}</p>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")
        
        # Quick actions
        st.markdown("## 🚀 Quick Actions")
        
        # Stock lookup
        stock_symbol = st.text_input("Enter Stock Symbol:", placeholder="e.g., AAPL")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Analyze"):
                if stock_symbol:
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"Analyze {stock_symbol.upper()}"
                    })
                    st.rerun()
        
        with col2:
            if st.button("💡 Recommend"):
                if stock_symbol:
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"Should I buy, hold, or sell {stock_symbol.upper()}?"
                    })
                    st.rerun()
        
        # Popular stocks
        st.markdown("## 🔥 Popular Stocks")
        for stock in st.session_state.popular_stocks:
            if st.button(f"📈 {stock}", key=f"popular_{stock}"):
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"What's the latest on {stock}?"
                })
                st.rerun()
        
        # Market summary
        if st.button("📰 Market Summary"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Give me a summary of current market conditions"
            })
            st.rerun()
        
        # Data refresh
        st.markdown("## 🔄 Data Management")
        if st.button("🔄 Refresh Data"):
            if check_rate_limit_streamlit():
                with st.spinner("Refreshing financial data..."):
                    data_ingestion.update_news_data()
                    data_ingestion.update_stock_data(st.session_state.popular_stocks)
                    st.success("Data refreshed!")
        
        # Rate limit information
        display_rate_limit_info()

def display_chat_interface():
    """Display the main chat interface"""
    st.markdown("""
    <div class="main-header">
        <h1>📈 AI Stock Market Assistant</h1>
        <p>Your intelligent companion for stock market analysis and investment insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about stocks, markets, or investments..."):
        # Check rate limit before processing
        if not check_rate_limit_streamlit():
            return
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing market data..."):
                try:
                    # Get response from the agent
                    response = stock_agent.answer_question(prompt)
                    
                    # Display response with typing effect
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    # Simulate typing effect
                    for chunk in response.split():
                        full_response += chunk + " "
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.05)
                    
                    message_placeholder.markdown(full_response)
                    
                    # Add assistant response to session state
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_message = f"I apologize, but I encountered an error: {str(e)}\n\nPlease ensure your API keys are configured correctly."
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})

def display_examples():
    """Display example questions users can ask"""
    st.markdown("## 💡 Example Questions")
    
    examples = [
        "What's the current price of Apple stock?",
        "Should I invest in Tesla right now?",
        "What are the latest market trends?",
        "Compare Microsoft and Google stocks",
        "What's happening with tech stocks today?",
        "Give me news about Amazon",
        "Is it a good time to buy Netflix?",
        "What are the best performing stocks this week?"
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(f"💭 {example}", key=f"example_{i}"):
                st.session_state.messages.append({
                    "role": "user",
                    "content": example
                })
                st.rerun()

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Check API keys
    try:
        config.validate_required_keys()
    except ValueError as e:
        st.error(f"❌ Configuration Error: {str(e)}")
        st.info("💡 Please set up your API keys in the environment variables or .env file")
        st.code("""
# Required API Keys:
GROQ_API_KEY=your_groq_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
NEWS_API_KEY=your_news_api_key_here
        """)
        return
    
    # Initialize data
    initialize_data()
    
    # Display sidebar
    display_sidebar()
    
    # Display main chat interface
    display_chat_interface()
    
    # Display examples if no conversation started
    if len(st.session_state.messages) == 1:  # Only initial message
        display_examples()
    
    # Auto-refresh data periodically (in production, use background tasks)
    if st.session_state.data_initialized:
        current_time = time.time()
        if hasattr(st.session_state, 'last_auto_refresh'):
            if current_time - st.session_state.last_auto_refresh > 1800:  # 30 minutes
                with st.spinner("Auto-refreshing data..."):
                    data_ingestion.update_news_data()
                    st.session_state.last_auto_refresh = current_time
        else:
            st.session_state.last_auto_refresh = current_time

if __name__ == "__main__":
    main() 