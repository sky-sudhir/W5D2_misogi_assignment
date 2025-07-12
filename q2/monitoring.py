import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from langsmith import Client
from langsmith.run_helpers import trace
from config import config

class LangSmithMonitor:
    """LangSmith monitoring and analytics"""
    
    def __init__(self):
        self.client = None
        self.enabled = False
        
        # Initialize LangSmith if configured
        if config.LANGCHAIN_TRACING_V2 and config.LANGCHAIN_API_KEY:
            try:
                # Set environment variables for LangSmith
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_ENDPOINT"] = config.LANGCHAIN_ENDPOINT
                os.environ["LANGCHAIN_API_KEY"] = config.LANGCHAIN_API_KEY
                os.environ["LANGCHAIN_PROJECT"] = config.LANGCHAIN_PROJECT
                
                self.client = Client()
                self.enabled = True
                print("✅ LangSmith monitoring enabled")
                
            except Exception as e:
                print(f"❌ Failed to initialize LangSmith: {e}")
                self.enabled = False
        else:
            print("ℹ️  LangSmith monitoring disabled (missing configuration)")
    
    def log_agent_interaction(self, 
                            user_input: str, 
                            agent_response: str, 
                            tools_used: List[str] = None,
                            execution_time: float = None,
                            error: Optional[str] = None) -> None:
        """Log agent interaction to LangSmith"""
        if not self.enabled:
            return
        
        try:
            metadata = {
                "user_input": user_input,
                "agent_response": agent_response,
                "tools_used": tools_used or [],
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "error": error,
                "session_type": "streamlit_chat"
            }
            
            # Create a run in LangSmith
            run_id = self.client.create_run(
                name="stock_market_agent_interaction",
                run_type="chain",
                inputs={"user_input": user_input},
                outputs={"agent_response": agent_response},
                extra=metadata
            )
            
        except Exception as e:
            print(f"Error logging to LangSmith: {e}")
    
    def log_tool_usage(self, 
                      tool_name: str, 
                      tool_input: str, 
                      tool_output: str,
                      execution_time: float = None,
                      error: Optional[str] = None) -> None:
        """Log tool usage to LangSmith"""
        if not self.enabled:
            return
        
        try:
            metadata = {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output": tool_output,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "error": error
            }
            
            self.client.create_run(
                name=f"tool_usage_{tool_name}",
                run_type="tool",
                inputs={"input": tool_input},
                outputs={"output": tool_output},
                extra=metadata
            )
            
        except Exception as e:
            print(f"Error logging tool usage to LangSmith: {e}")
    
    def log_data_ingestion(self, 
                          data_type: str, 
                          records_processed: int,
                          success: bool = True,
                          error: Optional[str] = None) -> None:
        """Log data ingestion events"""
        if not self.enabled:
            return
        
        try:
            metadata = {
                "data_type": data_type,
                "records_processed": records_processed,
                "success": success,
                "timestamp": datetime.now().isoformat(),
                "error": error
            }
            
            self.client.create_run(
                name=f"data_ingestion_{data_type}",
                run_type="chain",
                inputs={"data_type": data_type},
                outputs={"records_processed": records_processed, "success": success},
                extra=metadata
            )
            
        except Exception as e:
            print(f"Error logging data ingestion to LangSmith: {e}")
    
    def get_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get analytics from LangSmith"""
        if not self.enabled:
            return {"error": "LangSmith not enabled"}
        
        try:
            # Get runs from the last N hours
            runs = list(self.client.list_runs(
                project_name=config.LANGCHAIN_PROJECT,
                limit=100
            ))
            
            # Process analytics
            total_interactions = len(runs)
            successful_runs = sum(1 for run in runs if run.status == "success")
            failed_runs = total_interactions - successful_runs
            
            # Calculate average execution time
            execution_times = [run.execution_time for run in runs if run.execution_time]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            # Tool usage statistics
            tool_usage = {}
            for run in runs:
                if run.run_type == "tool":
                    tool_name = run.name.replace("tool_usage_", "")
                    tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
            
            return {
                "total_interactions": total_interactions,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": successful_runs / total_interactions if total_interactions > 0 else 0,
                "avg_execution_time": avg_execution_time,
                "tool_usage": tool_usage
            }
            
        except Exception as e:
            return {"error": f"Failed to get analytics: {e}"}

class PerformanceTracker:
    """Track application performance metrics"""
    
    def __init__(self):
        self.metrics = {
            "requests_count": 0,
            "total_response_time": 0,
            "errors_count": 0,
            "tool_usage": {},
            "start_time": time.time()
        }
    
    def track_request(self, response_time: float, success: bool = True):
        """Track a request"""
        self.metrics["requests_count"] += 1
        self.metrics["total_response_time"] += response_time
        
        if not success:
            self.metrics["errors_count"] += 1
    
    def track_tool_usage(self, tool_name: str):
        """Track tool usage"""
        self.metrics["tool_usage"][tool_name] = self.metrics["tool_usage"].get(tool_name, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        uptime = time.time() - self.metrics["start_time"]
        avg_response_time = (
            self.metrics["total_response_time"] / self.metrics["requests_count"]
            if self.metrics["requests_count"] > 0 else 0
        )
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.metrics["requests_count"],
            "total_errors": self.metrics["errors_count"],
            "error_rate": self.metrics["errors_count"] / self.metrics["requests_count"] if self.metrics["requests_count"] > 0 else 0,
            "avg_response_time": avg_response_time,
            "requests_per_minute": self.metrics["requests_count"] / (uptime / 60) if uptime > 0 else 0,
            "tool_usage": self.metrics["tool_usage"]
        }

class MonitoringDecorator:
    """Decorator for monitoring function calls"""
    
    def __init__(self, monitor: LangSmithMonitor, tracker: PerformanceTracker):
        self.monitor = monitor
        self.tracker = tracker
    
    def track_agent_call(self, func):
        """Decorator to track agent calls"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                execution_time = time.time() - start_time
                self.tracker.track_request(execution_time, success)
                
                # Log to LangSmith if it's an agent interaction
                if hasattr(func, '__name__') and 'answer_question' in func.__name__:
                    user_input = args[0] if args else kwargs.get('question', '')
                    agent_response = result if success else f"Error: {error}"
                    
                    self.monitor.log_agent_interaction(
                        user_input=user_input,
                        agent_response=agent_response,
                        execution_time=execution_time,
                        error=error
                    )
        
        return wrapper
    
    def track_tool_call(self, tool_name: str):
        """Decorator to track tool calls"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    result = func(*args, **kwargs)
                    self.tracker.track_tool_usage(tool_name)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    execution_time = time.time() - start_time
                    
                    tool_input = str(args[0]) if args else ""
                    tool_output = str(result) if success else f"Error: {error}"
                    
                    self.monitor.log_tool_usage(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        tool_output=tool_output,
                        execution_time=execution_time,
                        error=error
                    )
            
            return wrapper
        return decorator

# Global monitoring instances
langsmith_monitor = LangSmithMonitor()
performance_tracker = PerformanceTracker()
monitoring_decorator = MonitoringDecorator(langsmith_monitor, performance_tracker) 