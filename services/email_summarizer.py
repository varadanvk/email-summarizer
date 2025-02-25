import os
import base64
import openai  # For summarization

class EmailSummarizer:
    def __init__(self, credentials_file="credentials.json", token_file="token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None
    
    def authenticate(self):
        from services.google_auth import Authenticator
        auth = Authenticator(self.credentials_file)
        self.creds = auth.get_credentials()
        if not self.creds:
            print("No valid credentials found.")
            self.creds = auth.create_token()
        return self.creds
    
    def setup_service(self):
        from googleapiclient.discovery import build
        self.service = build("gmail", "v1", credentials=self.creds)
    
    def get_recent_emails(self, max_results=20):
        """Fetch the most recent emails from the inbox"""
        try:
            results = self.service.users().messages().list(
                userId="me", 
                maxResults=max_results
            ).execute()
            messages = results.get("messages", [])
            print(f"Fetched {len(messages)} recent messages.")
            return messages
        except Exception as error:
            print(f"An error occurred while fetching messages: {error}")
            return []
    
    def get_message_details(self, message_id):
        """Get the full details of a specific message"""
        try:
            message = self.service.users().messages().get(
                userId="me", 
                id=message_id
            ).execute()
            return message
        except Exception as error:
            print(f"An error occurred while fetching message details: {error}")
            return None
    
    def extract_email_content(self, message):
        """Extract the relevant content from an email message"""
        if not message or 'payload' not in message:
            return None
        
        headers = {}
        for header in message['payload'].get('headers', []):
            headers[header['name']] = header['value']
        
        # Get email body
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        
        return {
            'id': message['id'],
            'subject': headers.get('Subject', ''),
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'date': headers.get('Date', ''),
            'body': body,
            'snippet': message.get('snippet', '')
        }
    
    def summarize_email(self, email_content, max_length=100):
        """Generate a concise summary of the email content using OpenAI"""
        try:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            client = openai.OpenAI() # Instantiate OpenAI client

            # Create a prompt for the summarization
            prompt = f"""
            Please summarize the following email in a concise way (no more than {max_length} words):
            
            From: {email_content['from']}
            Subject: {email_content['subject']}
            Date: {email_content['date']}
            
            {email_content['body']}
            """
            
            response = client.chat.completions.create( # Use openai.chat.completions.create
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes emails concisely."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip() # Access message content using .content
            return summary
        except Exception as e:
            print(f"Error generating summary: {e}")
            # Fallback to a simple summary if the API call fails
            return f"Email from {email_content['from']} about '{email_content['subject']}'"
    
    def process_emails(self, max_results=20):
        """Process emails: fetch, extract content, and summarize"""
        self.authenticate()
        self.setup_service()
        
        messages = self.get_recent_emails(max_results)
        
        email_summaries = []
        for message in messages:
            details = self.get_message_details(message['id'])
            if details:
                email_content = self.extract_email_content(details)
                if email_content:
                    summary = self.summarize_email(email_content)
                    email_summaries.append({
                        'id': email_content['id'],
                        'from': email_content['from'],
                        'subject': email_content['subject'],
                        'date': email_content['date'],
                        'summary': summary,
                        'full_content': email_content
                    })
        
        return email_summaries 