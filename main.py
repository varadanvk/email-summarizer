import os
import json
import logging
from services.email_summarizer import EmailSummarizer
from services.text_notifier import TextNotifier
from dotenv import load_dotenv

logging.basicConfig(filename='email_summary.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')



def summarize_and_notify_emails(max_emails=20, importance_criteria=None):
    """Summarize recent emails and send important ones via text"""
    try:
        logging.info("Starting email summarization and notification process")
        
        # Initialize services
        email_summarizer = EmailSummarizer()
        text_notifier = TextNotifier()
        
        # Process emails
        email_summaries = email_summarizer.process_emails(max_results=max_emails)
        
        if not email_summaries:
            logging.warning("No emails were processed")
            return {"message": "No emails were processed"}
        
        # Print all email summaries
        print("All email summaries:")
        for i, summary in enumerate(email_summaries):
            print(f"\n--- Email {i+1} ---")
            print(f"Subject: {summary.get('subject', 'No subject')}")
            print(f"From: {summary.get('from', 'Unknown sender')}")
            print(f"Summary: {summary.get('summary', 'No summary available')}")
            print(f"Importance: {summary.get('importance', 'Not rated')}")
        
        # Save summaries to file for reference
        os.makedirs('outputs', exist_ok=True)
        with open('outputs/email_summaries.json', 'w') as f:
            json.dump(email_summaries, f, indent=2)
        
        # Send notifications for important emails
        notifications = text_notifier.notify_important_emails(
            email_summaries, 
            importance_criteria
        )
        
        if notifications:
            logging.info(f"Sent notifications for {len(notifications)} important emails")
            return {"message": f"Sent notifications for {len(notifications)} important emails"}
        else:
            logging.info("No important emails found requiring notification")
            return {"message": "No important emails found requiring notification"}
            
    except Exception as e:
        logging.error(f"An error occurred during email processing: {str(e)}", exc_info=True)
        return {"message": f"Error: {str(e)}"}

def main():
    try:
        load_dotenv()
        
        # Run email summarization and notification
        result = summarize_and_notify_emails(max_emails=20)
        print(f"\nFinal result: {result['message']}")
        return result

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return {"message": f"Error: {str(e)}"}

if __name__ == "__main__":
    main()
