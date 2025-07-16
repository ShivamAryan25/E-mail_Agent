import base64
import logging
from email import message_from_bytes
from datetime import date
from email.header import decode_header

def get_new_emails(service, sender_list, processed_label_name):
    today_str = date.today().strftime('%Y/%m/%d')
    from_query = " OR ".join([f"from:{sender}" for sender in sender_list])
    query = f"({from_query}) -label:{processed_label_name} after:{today_str}"
    
    logging.info(f"Executing Gmail query: {query}")
    
    try:
        response = service.users().messages().list(userId='me', q=query).execute()
        messages = response.get('messages', [])
        
        emails = []
        if not messages:
            return emails

        for msg in messages:
            msg_id = msg['id']
            msg_content = service.users().messages().get(userId='me', id=msg_id, format='raw').execute()
            
            raw_email = base64.urlsafe_b64decode(msg_content['raw'].encode('ASCII'))
            email_message = message_from_bytes(raw_email)
            
            subject = ""
            if email_message['subject']:
                try:
                    decoded_subject = decode_header(email_message['subject'])
                    subject_parts = []
                    for part, encoding in decoded_subject:
                        if isinstance(part, bytes):
                            subject_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
                        else:
                            subject_parts.append(part)
                    subject = "".join(subject_parts)
                except Exception:
                    subject = email_message['subject']

            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    disposition = str(part.get("Content-Disposition"))

                    if content_type == 'text/plain' and "attachment" not in disposition:
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break 
                        except Exception:
                            continue
            else:
                try:
                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                except Exception:
                    body = ""
            
            emails.append({'id': msg_id, 'subject': subject, 'body': body.strip()})
        
        return emails
    except Exception as e:
        logging.error(f"An error occurred while fetching emails: {e}")
        return []

def create_label_if_not_exists(service, label_name):
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    for label in labels:
        if label['name'] == label_name:
            logging.info(f"Label '{label_name}' already exists.")
            return label['id']

    logging.info(f"Label '{label_name}' not found, creating it.")
    label_body = {'name': label_name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
    created_label = service.users().labels().create(userId='me', body=label_body).execute()
    return created_label['id']

def apply_label_to_email(service, email_id, label_id):
    try:
        body = {'addLabelIds': [label_id], 'removeLabelIds': []}
        service.users().messages().modify(userId='me', id=email_id, body=body).execute()
        logging.info(f"Successfully applied label to email ID: {email_id}")
    except Exception as e:
        logging.error(f"Failed to apply label to email ID {email_id}: {e}")
