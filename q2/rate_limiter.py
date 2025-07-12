import time
from typing import Dict, List, Optional
from collections import defaultdict, deque
from threading import Lock
import streamlit as st
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, FastAPI
from fastapi.responses import PlainTextResponse

from config import config

class StreamlitRateLimiter:
    """Rate limiter for Streamlit applications"""
    
    def __init__(self, max_requests: int = None, window_seconds: int = 60):
        self.max_requests = max_requests or config.MAX_REQUESTS_PER_MINUTE
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = Lock()
    
    def is_allowed(self, identifier: str = None) -> bool:
        """Check if request is allowed for the given identifier"""
        if identifier is None:
            # Use session state as identifier for Streamlit
            identifier = st.session_state.get('session_id', 'default')
        
        current_time = time.time()
        
        with self.lock:
            # Clean old requests outside the window
            request_times = self.requests[identifier]
            while request_times and current_time - request_times[0] > self.window_seconds:
                request_times.popleft()
            
            # Check if under limit
            if len(request_times) < self.max_requests:
                request_times.append(current_time)
                return True
            
            return False
    
    def get_remaining_requests(self, identifier: str = None) -> int:
        """Get remaining requests for the identifier"""
        if identifier is None:
            identifier = st.session_state.get('session_id', 'default')
        
        current_time = time.time()
        
        with self.lock:
            request_times = self.requests[identifier]
            # Clean old requests
            while request_times and current_time - request_times[0] > self.window_seconds:
                request_times.popleft()
            
            return max(0, self.max_requests - len(request_times))
    
    def get_reset_time(self, identifier: str = None) -> Optional[float]:
        """Get time when rate limit resets"""
        if identifier is None:
            identifier = st.session_state.get('session_id', 'default')
        
        current_time = time.time()
        
        with self.lock:
            request_times = self.requests[identifier]
            if request_times:
                return request_times[0] + self.window_seconds
            return None

class FastAPIRateLimiter:
    """Rate limiter for FastAPI applications"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.limiter = Limiter(key_func=get_remote_address)
        self.app.state.limiter = self.limiter
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    def add_rate_limit(self, route_func, limit: str = None):
        """Add rate limit to a route function"""
        if limit is None:
            limit = f"{config.MAX_REQUESTS_PER_MINUTE}/minute"
        
        return self.limiter.limit(limit)(route_func)

class RequestTracker:
    """Track and monitor API requests"""
    
    def __init__(self):
        self.request_history = defaultdict(list)
        self.lock = Lock()
    
    def log_request(self, identifier: str, endpoint: str, success: bool = True):
        """Log a request"""
        with self.lock:
            self.request_history[identifier].append({
                'timestamp': time.time(),
                'endpoint': endpoint,
                'success': success
            })
    
    def get_request_stats(self, identifier: str, hours: int = 24) -> Dict:
        """Get request statistics for an identifier"""
        cutoff_time = time.time() - (hours * 3600)
        
        with self.lock:
            requests = self.request_history.get(identifier, [])
            recent_requests = [r for r in requests if r['timestamp'] > cutoff_time]
            
            total_requests = len(recent_requests)
            successful_requests = sum(1 for r in recent_requests if r['success'])
            failed_requests = total_requests - successful_requests
            
            return {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': successful_requests / total_requests if total_requests > 0 else 0
            }

# Rate limiter decorators for different use cases
def rate_limit_decorator(limiter: StreamlitRateLimiter):
    """Decorator to apply rate limiting to functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not limiter.is_allowed():
                remaining = limiter.get_remaining_requests()
                reset_time = limiter.get_reset_time()
                
                if reset_time:
                    wait_time = int(reset_time - time.time())
                    st.error(f"🚫 Rate limit exceeded. Please wait {wait_time} seconds before trying again.")
                    st.info(f"💡 You have {remaining} requests remaining.")
                    return None
                else:
                    st.error("🚫 Rate limit exceeded. Please try again later.")
                    return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def check_rate_limit_streamlit() -> bool:
    """Check rate limit for Streamlit requests"""
    if 'rate_limiter' not in st.session_state:
        st.session_state.rate_limiter = StreamlitRateLimiter()
    
    limiter = st.session_state.rate_limiter
    
    if not limiter.is_allowed():
        remaining = limiter.get_remaining_requests()
        reset_time = limiter.get_reset_time()
        
        if reset_time:
            wait_time = int(reset_time - time.time())
            st.error(f"🚫 Rate limit exceeded. You can make {config.MAX_REQUESTS_PER_MINUTE} requests per minute.")
            st.info(f"⏰ Please wait {wait_time} seconds before trying again.")
            st.info(f"💡 Remaining requests: {remaining}")
        else:
            st.error("🚫 Rate limit exceeded. Please try again later.")
        
        return False
    
    return True

def display_rate_limit_info():
    """Display rate limit information in Streamlit"""
    if 'rate_limiter' not in st.session_state:
        st.session_state.rate_limiter = StreamlitRateLimiter()
    
    limiter = st.session_state.rate_limiter
    remaining = limiter.get_remaining_requests()
    
    # Display in sidebar
    with st.sidebar:
        st.markdown("## ⚡ Rate Limit Status")
        
        # Progress bar for remaining requests
        progress = remaining / config.MAX_REQUESTS_PER_MINUTE
        st.progress(progress)
        
        st.markdown(f"""
        <div style="text-align: center; padding: 0.5rem;">
            <strong>{remaining}/{config.MAX_REQUESTS_PER_MINUTE}</strong> requests remaining
        </div>
        """, unsafe_allow_html=True)
        
        if remaining < 3:
            st.warning("⚠️ Approaching rate limit!")

# Global instances
streamlit_rate_limiter = StreamlitRateLimiter()
request_tracker = RequestTracker() 