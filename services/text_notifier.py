import os
from twilio.rest import Client

class TextNotifier:
    def __init__(self, account_sid=None, auth_token=None, from_number=None, to_number=None):
        """Initialize the TextNotifier with Twilio credentials"""
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_FROM_NUMBER")
        self.to_number = to_number or os.getenv("TWILIO_TO_NUMBER")
        
        if not all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
            print("Warning: Twilio credentials are not fully configured. Text notifications may not work.")
        
        self.client = None
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
    
    def is_important(self, email_data, importance_criteria=None):
        """Determine if an email is important based on the given criteria"""
        if not importance_criteria:
            # Default criteria - adjust as needed
            importance_criteria = {
                # High priority senders
                'from': ['boss@company.com', 'urgent', 'important'],
                
                # Important subject keywords
                'subject': ['urgent', 'important', 'action required', 'deadline'],
                
                # Body content keywords
                'body': ['urgent', 'asap', 'deadline', 'tomorrow']
            }
        
        # Check sender
        sender = email_data.get('from', '').lower()
        if any(term.lower() in sender for term in importance_criteria.get('from', [])):
            return True
        
        # Check subject
        subject = email_data.get('subject', '').lower()
        if any(term.lower() in subject for term in importance_criteria.get('subject', [])):
            return True
        
        # Check body content
        body = email_data.get('full_content', {}).get('body', '').lower()
        if any(term.lower() in body for term in importance_criteria.get('body', [])):
            return True
        
        return False
    
    def send_text(self, message):
        """Send a text message using Twilio"""
        if not self.client:
            print("Error: Twilio client not initialized. Check your credentials.")
            return False
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )
            
            print(f"Text message sent successfully. SID: {message.sid}")
            return True
        except Exception as e:
            print(f"Error sending text message: {e}")
            return False
    
    def notify_important_emails(self, email_summaries, importance_criteria=None):
        """Send text notifications for important emails"""
        important_emails = [
            email for email in email_summaries 
            if self.is_important(email, importance_criteria)
        ]
        
        if not important_emails:
            print("No important emails to notify about.")
            return []
        
        notifications_sent = []
        for email in important_emails:
            message = f"IMPORTANT EMAIL:\nFrom: {email['from']}\nSubject: {email['subject']}\n\n{email['summary']}"
            
            # Truncate if too long for SMS
            if len(message) > 1500:
                message = message[:1497] + "..."
                
            success = self.send_text(message)
            if success:
                notifications_sent.append(email)
        
        return notifications_sent 