# Gmail API Setup Guide

This guide will help you set up Gmail API authentication for the Gmail implementation.

## Prerequisites

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Gmail API Setup

### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click on it and press "Enable"

### Step 2: Create Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" for user type
   - Fill in the required fields (App name, User support email, Developer contact)
   - Add your email to test users
4. For Application type, choose "Desktop application"
5. Give it a name (e.g., "Gmail MCP Client")
6. Click "Create"

### Step 3: Download Credentials

1. Download the JSON file containing your credentials
2. Rename it to `credentials.json`
3. Place it in the `backend/` directory

### Step 4: Set up OAuth Scopes

The implementation uses these scopes:
- `https://www.googleapis.com/auth/gmail.readonly` - Read emails
- `https://www.googleapis.com/auth/gmail.send` - Send emails
- `https://www.googleapis.com/auth/gmail.modify` - Modify emails (mark as read, etc.)

### Step 5: First Run Authentication

1. Run the implementation file:
```bash
cd backend
python gmail_implementation.py
```

2. This will open a browser window for OAuth authentication
3. Sign in with your Google account
4. Grant the requested permissions
5. The authentication token will be saved as `token.json`

## Usage Examples

### Search Emails

```python
from gmail_implementation import GmailService

gmail = GmailService()

# Search for unread emails
results = gmail.search_emails("is:unread", max_results=10)

# Search by sender
results = gmail.search_emails("from:example@gmail.com")

# Search by subject
results = gmail.search_emails("subject:important")

# Complex search
results = gmail.search_emails("from:boss@company.com is:unread")
```

### Send Email

```python
from gmail_implementation import GmailService

gmail = GmailService()

result = gmail.send_email(
    to="recipient@example.com",
    subject="Test Email",
    body="This is a test email sent via Gmail API",
    cc="cc@example.com",  # Optional
    bcc="bcc@example.com"  # Optional
)

print(result)
```

### Integration with MCP Server

The `gmail_implementation.py` file provides convenience functions that can be used in your MCP server:

```python
from gmail_implementation import search_emails_impl, send_email_impl

# In your MCP server
@mcp.tool()
def search_emails(query: str) -> str:
    return search_emails_impl(query)

@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    return send_email_impl(to, subject, body)
```

## File Structure

After setup, your backend directory should look like this:

```
backend/
├── gmail_implementation.py  # Main implementation
├── gmail_mcp.py            # MCP server
├── credentials.json        # OAuth credentials (keep private)
├── token.json             # Access token (auto-generated)
└── GMAIL_SETUP.md         # This setup guide
```

## Important Notes

1. **Keep credentials.json private** - Never commit this file to version control
2. **token.json** is auto-generated and refreshed automatically
3. The first run requires manual authentication in a browser
4. Subsequent runs will use the saved token
5. If authentication fails, delete `token.json` and run again

## Troubleshooting

### "Credentials file not found"
- Make sure `credentials.json` is in the `backend/` directory
- Verify the file is properly formatted JSON

### "Authentication failed"
- Delete `token.json` and try again
- Check that your Google Cloud project has Gmail API enabled
- Verify your OAuth consent screen is configured

### "Access denied"
- Make sure your email is added to test users in the OAuth consent screen
- Check that the required scopes are enabled in your Google Cloud project

## Security Considerations

1. Store credentials securely
2. Use environment variables for production deployments
3. Implement proper error handling
4. Consider rate limiting for production use
5. Review and minimize required scopes 