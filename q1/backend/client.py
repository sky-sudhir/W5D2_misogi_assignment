import os
import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# Set your Groq API key here or export as environment variable
# os.environ["GROQ_API_KEY"] = "gsk_your_groq_api_key"

# MCP server connection parameters
server_params = {
    "url": "http://localhost:8000/mcp",
    "headers": {
        # If your MCP server requires API key or auth, add here, e.g.:
        # "X-Api-Key": "your_mcp_api_key"
    }
}

async def main():
    # Initialize Groq LLM
    llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct")

    # Connect to MCP server and load Gmail tools
    async with streamablehttp_client(**server_params) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            print(f"Loaded MCP tools: {[tool.name for tool in tools]}")

            # Create LangChain agent with Groq LLM and Gmail tools
            agent = create_react_agent(llm, tools)

            # Example: ask agent to search emails
            user_message = "Search my emails for meeting notes from last week."
            response = await agent.ainvoke({
                "messages": [{"role": "user", "content": user_message}]
            })
            parser = StrOutputParser()
            print("Agent response:", parser.parse(response))

if __name__ == "__main__":
    asyncio.run(main())
