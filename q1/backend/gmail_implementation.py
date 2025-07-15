import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
import logging

# Gmail API imports (you'll need to install these)
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Gmail API libraries not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

class GmailService:
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        """
        Initialize Gmail service with authentication.
        
        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to store/load access token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.logger = logging.getLogger(__name__)
        
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                self.logger.error(f"Error loading token: {e}")
                
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.error(f"Error refreshing token: {e}")
                    creds = None
                    
            if not creds:
                if not os.path.exists(self.credentials_file):
                    self.logger.error(f"Credentials file not found: {self.credentials_file}")
                    return False
                    
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    self.logger.error(f"Error during OAuth flow: {e}")
                    return False
                    
            # Save credentials for next run
            try:
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                self.logger.error(f"Error saving token: {e}")
                
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except Exception as e:
            self.logger.error(f"Error building Gmail service: {e}")
            return False
            
    def search_emails(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search emails using Gmail search query syntax.
        
        Args:
            query: Gmail search query (e.g., "from:example@gmail.com", "subject:important")
            max_results: Maximum number of emails to return
            
        Returns:
            List of email dictionaries with id, threadId, snippet, and metadata
        """
        if not self.service:
            if not self.authenticate():
                return []
                
        try:
            # Search for messages
            results = self.service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return []
                
            # Get detailed information for each message
            detailed_messages = []
            for message in messages:
                try:
                    msg = self.service.users().messages().get(
                        userId='me', 
                        id=message['id']
                    ).execute()
                    
                    # Extract headers
                    headers = msg['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                    
                    # Extract body
                    body = self._extract_body(msg['payload'])
                    
                    detailed_messages.append({
                        'id': msg['id'],
                        'threadId': msg['threadId'],
                        'subject': subject,
                        'from': sender,
                        'date': date,
                        'snippet': msg.get('snippet', ''),
                        'body': body[:500] + '...' if len(body) > 500 else body,  # Truncate long bodies
                        'labels': msg.get('labelIds', [])
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error getting message details for {message['id']}: {e}")
                    
            return detailed_messages
            
        except HttpError as error:
            self.logger.error(f"Gmail API error during search: {error}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error during search: {e}")
            return []
            
    def _extract_body(self, payload: Dict) -> str:
        """
        Extract email body from message payload.
        
        Args:
            payload: Message payload from Gmail API
            
        Returns:
            Email body as string
        """
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                
        return body
        
    def send_email(self, to: str, subject: str, body: str, 
                   cc: Optional[str] = None, bcc: Optional[str] = None,
                   attachments: Optional[List[str]] = None) -> Dict:
        """
        Send an email using Gmail API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            attachments: List of file paths to attach
            
        Returns:
            Dictionary with send result and message ID
        """
        if not self.service:
            if not self.authenticate():
                return {'success': False, 'error': 'Authentication failed'}
                
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
                
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'rb') as attachment:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(attachment.read())
                                
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            message.attach(part)
                        except Exception as e:
                            self.logger.error(f"Error attaching file {file_path}: {e}")
                    else:
                        self.logger.warning(f"Attachment file not found: {file_path}")
                        
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send message
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                'success': True,
                'message_id': send_result['id'],
                'thread_id': send_result['threadId']
            }
            
        except HttpError as error:
            self.logger.error(f"Gmail API error during send: {error}")
            return {'success': False, 'error': str(error)}
        except Exception as e:
            self.logger.error(f"Unexpected error during send: {e}")
            return {'success': False, 'error': str(e)}
            
    def get_email_by_id(self, message_id: str) -> Optional[Dict]:
        """
        Get a specific email by its ID.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Email dictionary or None if not found
        """
        if not self.service:
            if not self.authenticate():
                return None
                
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()
            
            # Extract headers
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            # Extract body
            body = self._extract_body(msg['payload'])
            
            return {
                'id': msg['id'],
                'threadId': msg['threadId'],
                'subject': subject,
                'from': sender,
                'date': date,
                'snippet': msg.get('snippet', ''),
                'body': body,
                'labels': msg.get('labelIds', [])
            }
            
        except HttpError as error:
            self.logger.error(f"Gmail API error getting email {message_id}: {error}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting email {message_id}: {e}")
            return None
            
    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark an email as read.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            if not self.authenticate():
                return False
                
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
            
        except HttpError as error:
            self.logger.error(f"Gmail API error marking as read {message_id}: {error}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error marking as read {message_id}: {e}")
            return False


# Convenience functions for the MCP server
def search_emails_impl(query: str, max_results: int = 10) -> str:
    """
    Implementation of search_emails function for MCP server.
    
    Args:
        query: Gmail search query
        max_results: Maximum number of results to return
        
    Returns:
        JSON string with search results
    """
    gmail_service = GmailService()
    
    try:
        results = gmail_service.search_emails(query, max_results)
        
        if not results:
            return json.dumps({
                'success': True,
                'count': 0,
                'emails': [],
                'message': 'No emails found matching the query'
            })
            
        return json.dumps({
            'success': True,
            'count': len(results),
            'emails': results,
            'message': f'Found {len(results)} emails'
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': str(e),
            'message': 'Error searching emails'
        })


def send_email_impl(to: str, subject: str, body: str, 
                   cc: Optional[str] = None, bcc: Optional[str] = None) -> str:
    """
    Implementation of send_email function for MCP server.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
        
    Returns:
        JSON string with send result
    """
    gmail_service = GmailService()
    
    try:
        result = gmail_service.send_email(to, subject, body, cc, bcc)
        
        if result['success']:
            return json.dumps({
                'success': True,
                'message_id': result['message_id'],
                'thread_id': result['thread_id'],
                'message': f'Email sent successfully to {to}'
            })
        else:
            return json.dumps({
                'success': False,
                'error': result['error'],
                'message': 'Failed to send email'
            })
            
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': str(e),
            'message': 'Error sending email'
        })


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    gmail = GmailService()
    
    # Test search
    print("Testing email search...")
    results = gmail.search_emails("is:unread", max_results=5)
    print(f"Found {len(results)} unread emails")
    
    # Test send (uncomment to test)
    # print("Testing email send...")
    # send_result = gmail.send_email(
    #     to="test@example.com",
    #     subject="Test Email",
    #     body="This is a test email sent via Gmail API"
    # )
    # print(f"Send result: {send_result}") 