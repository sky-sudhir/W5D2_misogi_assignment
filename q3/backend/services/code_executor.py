import asyncio
import time
from typing import Callable, Optional
from e2b import Sandbox
import logging
from models.schemas import ExecutionResult, ExecutionStatus, Language

logger = logging.getLogger(__name__)

class CodeExecutor:
    def __init__(self):
        self.sandbox_templates = {
            Language.PYTHON: "python3",
            Language.JAVASCRIPT: "nodejs"
        }
    
    async def execute_code(
        self, 
        code: str, 
        language: Language, 
        output_callback: Optional[Callable[[str], None]] = None,
        timeout: int = 30
    ) -> ExecutionResult:
        """Execute code in E2B sandbox with streaming output"""
        
        start_time = time.time()
        stdout_buffer = []
        stderr_buffer = []
        
        try:
            # Get appropriate sandbox template
            template = self.sandbox_templates.get(language)
            if not template:
                raise ValueError(f"Unsupported language: {language}")
            
            # Create sandbox
            sandbox = Sandbox(template=template)
            
            try:
                if language == Language.PYTHON:
                    result = await self._execute_python(
                        sandbox, code, output_callback, stdout_buffer, stderr_buffer
                    )
                elif language == Language.JAVASCRIPT:
                    result = await self._execute_javascript(
                        sandbox, code, output_callback, stdout_buffer, stderr_buffer
                    )
                else:
                    raise ValueError(f"Unsupported language: {language}")
                
                execution_time = time.time() - start_time
                
                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS if result.exit_code == 0 else ExecutionStatus.ERROR,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    execution_time=execution_time,
                    exit_code=result.exit_code,
                    error_message=result.stderr if result.exit_code != 0 else None
                )
                
            finally:
                # Clean up sandbox
                sandbox.close()
                
        except asyncio.TimeoutError:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                stdout="".join(stdout_buffer),
                stderr="Execution timed out",
                execution_time=timeout,
                error_message="Code execution timed out"
            )
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                stdout="".join(stdout_buffer),
                stderr=str(e),
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _execute_python(self, sandbox, code: str, output_callback, stdout_buffer, stderr_buffer):
        """Execute Python code in sandbox"""
        
        # Create a temporary Python file
        file_path = "/tmp/user_code.py"
        sandbox.files.write(file_path, code)
        
        # Execute with streaming output
        process = sandbox.process.start(
            f"python3 {file_path}",
            on_stdout=lambda data: self._handle_output(data, stdout_buffer, output_callback),
            on_stderr=lambda data: self._handle_output(data, stderr_buffer, output_callback, is_error=True)
        )
        
        # Wait for completion
        result = process.wait()
        return result
    
    async def _execute_javascript(self, sandbox, code: str, output_callback, stdout_buffer, stderr_buffer):
        """Execute JavaScript code in sandbox"""
        
        # Create a temporary JavaScript file
        file_path = "/tmp/user_code.js"
        sandbox.files.write(file_path, code)
        
        # Execute with streaming output
        process = sandbox.process.start(
            f"node {file_path}",
            on_stdout=lambda data: self._handle_output(data, stdout_buffer, output_callback),
            on_stderr=lambda data: self._handle_output(data, stderr_buffer, output_callback, is_error=True)
        )
        
        # Wait for completion
        result = process.wait()
        return result
    
    def _handle_output(self, data: str, buffer: list, callback: Optional[Callable], is_error: bool = False):
        """Handle streaming output from code execution"""
        buffer.append(data)
        if callback:
            callback({
                "type": "stderr" if is_error else "stdout",
                "data": data
            }) 