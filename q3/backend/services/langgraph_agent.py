import os
from typing import AsyncGenerator, Dict, Any, List, Optional
import logging
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
import asyncio

from models.schemas import ExecutionResult, Language
from services.rag_service import RAGService

logger = logging.getLogger(__name__)

class CodeTutorState(TypedDict):
    messages: List[Any]
    code: str
    language: str
    execution_result: ExecutionResult
    relevant_docs: List[Any]
    explanation: str
    current_step: str

class CodeTutorAgent:
    def __init__(self):
        # Initialize Groq LLM
        self.llm = ChatGroq(
            temperature=0.1,
            model_name="mixtral-8x7b-32768",  # or "llama2-70b-4096"
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Initialize RAG service
        self.rag_service = RAGService()
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        
        logger.info("CodeTutorAgent initialized with LangGraph workflow")
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for code tutoring"""
        
        # Define the workflow
        workflow = StateGraph(CodeTutorState)
        
        # Add nodes
        workflow.add_node("analyze_code", self._analyze_code)
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("generate_explanation", self._generate_explanation)
        workflow.add_node("format_response", self._format_response)
        
        # Add edges
        workflow.add_edge("analyze_code", "retrieve_context")
        workflow.add_edge("retrieve_context", "generate_explanation")
        workflow.add_edge("generate_explanation", "format_response")
        workflow.add_edge("format_response", END)
        
        # Set entry point
        workflow.set_entry_point("analyze_code")
        
        return workflow.compile()
    
    async def _analyze_code(self, state: CodeTutorState) -> CodeTutorState:
        """Analyze the code and execution result"""
        
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a code analysis expert. Analyze the provided code and execution result.
            
            Focus on:
            1. Code structure and logic
            2. Potential issues or improvements
            3. Key concepts demonstrated
            4. Error analysis (if any)
            
            Provide a concise analysis that will help with generating educational explanations."""),
            ("human", """
            Language: {language}
            Code:
            ```{language}
            {code}
            ```
            
            Execution Result:
            - Status: {status}
            - Output: {stdout}
            - Errors: {stderr}
            - Execution Time: {execution_time}s
            """)
        ])
        
        try:
            response = await self.llm.ainvoke(
                analysis_prompt.format_messages(
                    language=state["language"],
                    code=state["code"],
                    status=state["execution_result"].status,
                    stdout=state["execution_result"].stdout,
                    stderr=state["execution_result"].stderr,
                    execution_time=state["execution_result"].execution_time
                )
            )
            
            state["current_step"] = "Code analysis completed"
            state["messages"].append(response)
            
        except Exception as e:
            logger.error(f"Error in code analysis: {str(e)}")
            state["current_step"] = f"Error in analysis: {str(e)}"
        
        return state
    
    async def _retrieve_context(self, state: CodeTutorState) -> CodeTutorState:
        """Retrieve relevant context from RAG"""
        
        try:
            # Get relevant documents
            relevant_docs = await self.rag_service.get_relevant_context(
                code=state["code"],
                language=state["language"],
                error_message=state["execution_result"].stderr if state["execution_result"].stderr else None,
                k=3
            )
            
            state["relevant_docs"] = relevant_docs
            state["current_step"] = f"Retrieved {len(relevant_docs)} relevant documents"
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            state["relevant_docs"] = []
            state["current_step"] = f"Error retrieving context: {str(e)}"
        
        return state
    
    async def _generate_explanation(self, state: CodeTutorState) -> CodeTutorState:
        """Generate educational explanation"""
        
        # Prepare context from retrieved documents
        context_text = ""
        if state["relevant_docs"]:
            context_text = "\n\n".join([
                f"Reference {i+1}:\n{doc.page_content}"
                for i, doc in enumerate(state["relevant_docs"])
            ])
        
        explanation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert programming tutor. Provide a clear, educational explanation of the code and its execution.

            Your explanation should:
            1. Explain what the code does step-by-step
            2. Highlight key programming concepts
            3. Explain any errors and how to fix them
            4. Suggest improvements or best practices
            5. Use the provided reference materials when relevant
            
            Structure your response with clear sections and be educational but concise."""),
            ("human", """
            Language: {language}
            Code:
            ```{language}
            {code}
            ```
            
            Execution Result:
            - Status: {status}
            - Output: {stdout}
            - Errors: {stderr}
            - Execution Time: {execution_time}s
            
            Reference Materials:
            {context}
            
            Please provide a comprehensive explanation suitable for learning.
            """)
        ])
        
        try:
            response = await self.llm.ainvoke(
                explanation_prompt.format_messages(
                    language=state["language"],
                    code=state["code"],
                    status=state["execution_result"].status,
                    stdout=state["execution_result"].stdout,
                    stderr=state["execution_result"].stderr,
                    execution_time=state["execution_result"].execution_time,
                    context=context_text
                )
            )
            
            state["explanation"] = response.content
            state["current_step"] = "Explanation generated"
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            state["explanation"] = f"Error generating explanation: {str(e)}"
            state["current_step"] = f"Error: {str(e)}"
        
        return state
    
    async def _format_response(self, state: CodeTutorState) -> CodeTutorState:
        """Format the final response"""
        
        state["current_step"] = "Response formatted and ready"
        return state
    
    async def generate_explanation(
        self, 
        code: str, 
        language: str, 
        execution_result: ExecutionResult
    ) -> AsyncGenerator[str, None]:
        """Generate streaming explanation using LangGraph workflow"""
        
        # Initialize state
        initial_state = CodeTutorState(
            messages=[],
            code=code,
            language=language,
            execution_result=execution_result,
            relevant_docs=[],
            explanation="",
            current_step="Starting analysis..."
        )
        
        try:
            # Run the workflow
            async for event in self.workflow.astream(initial_state):
                for node_name, node_state in event.items():
                    if "current_step" in node_state:
                        # Stream progress updates
                        yield f"**{node_name}**: {node_state['current_step']}\n\n"
                        
                        # Small delay for streaming effect
                        await asyncio.sleep(0.1)
                    
                    # Stream the final explanation
                    if node_name == "generate_explanation" and "explanation" in node_state:
                        explanation = node_state["explanation"]
                        
                        # Stream explanation in chunks
                        chunk_size = 50
                        for i in range(0, len(explanation), chunk_size):
                            chunk = explanation[i:i + chunk_size]
                            yield chunk
                            await asyncio.sleep(0.05)  # Small delay for streaming effect
        
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}")
            yield f"Error generating explanation: {str(e)}"
    
    async def get_quick_help(self, code: str, language: str) -> str:
        """Get quick help for code without full workflow"""
        
        help_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful programming assistant. Provide quick help for the given code."),
            ("human", "Language: {language}\nCode:\n```{language}\n{code}\n```\n\nProvide quick help or suggestions.")
        ])
        
        try:
            response = await self.llm.ainvoke(
                help_prompt.format_messages(language=language, code=code)
            )
            return response.content
        except Exception as e:
            logger.error(f"Error getting quick help: {str(e)}")
            return f"Error getting help: {str(e)}" 