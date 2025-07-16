import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    logging.error(f"Failed to configure Gemini: {e}")
    model = None

def get_summary_and_deadline(email_body, email_subject):
    
    if not model:
        logging.error("Gemini model is not available.")
        return None

    # Limit the body length to avoid excessive API usage
    max_length = 8000
    if len(email_body) > max_length:
        email_body = email_body[:max_length] + "\n... (email truncated)"

    prompt = f"""
    Analyze the following email and provide a structured JSON output.

    **Instructions:**
    1.  Create a very short, one-line summary of the email's main point or call to action. This summary should be under 15 words and will be used as a task title.
    2.  Identify the deadline mentioned in the email. The deadline must be a specific date.
    3.  Format the extracted deadline as a string: "YYYY-MM-DD".
    4.  If no specific deadline date is found, the value for "deadline" must be null. Do not guess or infer a date.
    5.  Your entire response must be only a valid JSON object with the keys "summary" and "deadline".

    **Email Subject:** "{email_subject}"

    **Email Body:**
    ---
    {email_body}
    ---
    """
    
    try:
        logging.info("Sending request to Gemini API for a short summary...")
        response = model.generate_content(prompt)
        
        # Clean the response to extract the JSON part
        response_text = response.text.strip()
        json_str = response_text.replace("```json", "").replace("```", "").strip()
        
        # Parse the JSON string
        analysis = json.loads(json_str)

        # Basic validation of the returned structure
        if 'summary' in analysis and 'deadline' in analysis:
            return analysis
        else:
            logging.warning(f"Gemini response did not contain required keys. Response: {json_str}")
            return None

    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from Gemini response: {response.text}")
        return None
    except Exception as e:
        logging.error(f"An error occurred with the Gemini API: {e}")
        return None
