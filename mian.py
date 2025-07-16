import os
import time
import logging
from datetime import datetime

from google_auth import get_google_services
from gmail_service import get_new_emails, create_label_if_not_exists, apply_label_to_email
from gemini_service import get_summary_and_deadline
from tasks_service import get_task_list_id, create_task

EMAIL_LIST_FILE = "emails_to_track.txt"
TASK_LIST_NAME = "My Tasks"
PROCESSED_LABEL_NAME = "Processed-By-Agent"
CHECK_INTERVAL_SECONDS = 900

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_sender_emails(filename):
    try:
        with open(filename, 'r') as f:
            emails = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        if not emails:
            logging.error(f"'{filename}' is empty or contains no valid email entries. Exiting.")
            return None
        return emails
    except FileNotFoundError:
        logging.error(f"Error: The email list file '{filename}' was not found. Please create it. Exiting.")
        return None

def main():
    logging.info("--- Gmail to Tasks Agent Started ---")
    
    sender_emails = load_sender_emails(EMAIL_LIST_FILE)
    if not sender_emails:
        return

    try:
        gmail_service, tasks_service = get_google_services()
        logging.info("Successfully authenticated with Google services.")
    except Exception as e:
        logging.error(f"Failed to authenticate with Google services: {e}")
        return

    try:
        task_list_id = get_task_list_id(tasks_service, TASK_LIST_NAME)
        if not task_list_id:
            logging.error(f"Task list '{TASK_LIST_NAME}' not found. Please create it in Google Tasks.")
            return
        logging.info(f"Found Task List ID for '{TASK_LIST_NAME}': {task_list_id}")
    except Exception as e:
        logging.error(f"Error finding task list: {e}")
        return

    try:
        label_id = create_label_if_not_exists(gmail_service, PROCESSED_LABEL_NAME)
        logging.info(f"Using label '{PROCESSED_LABEL_NAME}' with ID: {label_id}")
    except Exception as e:
        logging.error(f"Error creating or finding Gmail label: {e}")
        return

    while True:
        try:
            logging.info(f"Checking for new emails from addresses in '{EMAIL_LIST_FILE}'")
            
            emails = get_new_emails(gmail_service, sender_emails, PROCESSED_LABEL_NAME)

            if not emails:
                logging.info("No new emails to process.")
            else:
                logging.info(f"Found {len(emails)} new emails to process.")

                for email_data in emails:
                    email_id = email_data['id']
                    email_subject = email_data['subject']
                    email_body = email_data['body']
                    
                    logging.info(f"Processing email: '{email_subject}' (ID: {email_id})")

                    if not email_body:
                        logging.warning("Email body is empty, skipping.")
                        apply_label_to_email(gmail_service, email_id, label_id)
                        continue
                    
                    try:
                        analysis = get_summary_and_deadline(email_body, email_subject)
                        if analysis and analysis.get('summary'):
                            summary = analysis['summary']
                            deadline = analysis.get('deadline')
                            
                            logging.info(f"Gemini Summary: '{summary}'")
                            if deadline:
                                logging.info(f"Gemini Found Deadline: {deadline}")

                            create_task(tasks_service, task_list_id, summary, deadline)
                            
                            apply_label_to_email(gmail_service, email_id, label_id)

                        else:
                            logging.warning(f"Could not generate a summary for email ID: {email_id}. Applying label to skip.")
                            apply_label_to_email(gmail_service, email_id, label_id)

                    except Exception as e:
                        logging.error(f"An error occurred during Gemini processing or Task creation for email ID {email_id}: {e}")

        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}")
        
        logging.info(f"Waiting for {CHECK_INTERVAL_SECONDS} seconds before next check.")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == '__main__':
    main()
