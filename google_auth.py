import os
import json
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify', 
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/gmail.labels'
]


CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_google_services():
    
    creds = None

    if os.path.exists(TOKEN_FILE):
        logging.info(f"Loading credentials from local file: {TOKEN_FILE}")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logging.info("Credentials have expired, refreshing token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                logging.error(f"Token refresh failed: {e}. You may need to re-authenticate by deleting token.json.")
                creds = None
        
        if not creds:
            logging.info("No valid credentials found, starting authentication flow...")
            
            flow = None
            if os.path.exists(CREDENTIALS_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            else:
                 raise FileNotFoundError(
                    "FATAL: Cannot authenticate. `credentials.json` not found."
                )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        logging.info(f"Credentials saved to {TOKEN_FILE}")

    gmail_service = build('gmail', 'v1', credentials=creds)
    tasks_service = build('tasks', 'v1', credentials=creds)
    
    return gmail_service, tasks_service
