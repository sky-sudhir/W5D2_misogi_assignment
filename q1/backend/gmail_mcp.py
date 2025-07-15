# gmail_mcp_server.py
from fastmcp import FastMCP
from gmail_implementation import search_emails_impl, send_email_impl

mcp = FastMCP("Gmail")

@mcp.tool()
def search_emails(query: str) -> str:
    """Search emails using Gmail API with the provided query."""
    return search_emails_impl(query)

@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email using Gmail API."""
    return send_email_impl(to, subject, body)

if __name__ == "__main__":
    # Run MCP server on stdio or streamable-http transport
     mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp",
        log_level="debug",
    )
