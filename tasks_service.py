import logging
from datetime import datetime, timedelta

def get_task_list_id(service, list_name):
    try:
        results = service.tasklists().list(maxResults=100).execute()
        items = results.get('items', [])
        for item in items:
            if item['title'] == list_name:
                return item['id']
        return None
    except Exception as e:
        logging.error(f"Could not retrieve task lists: {e}")
        return None

def create_task(service, task_list_id, summary, deadline_str=None):
    task = {
        'title': summary,
        'notes': 'Task automatically created from a Gmail email.'
    }

    if deadline_str:
        try:
            due_date = datetime.strptime(deadline_str, '%Y-%m-%d')
            task['due'] = due_date.isoformat() + "Z"
        except ValueError:
            logging.warning(f"Invalid deadline format '{deadline_str}'. Creating task without a due date.")
    
    try:
        result = service.tasks().insert(tasklist=task_list_id, body=task).execute()
        logging.info(f"Successfully created task: '{result['title']}' (ID: {result['id']})")
    except Exception as e:
        logging.error(f"Failed to create task: {e}")
