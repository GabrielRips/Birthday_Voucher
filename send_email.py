import json
import os
import time
import requests
import logging
import base64
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class MailerSendClient:
    def __init__(self, api_key, sender_email):
        self.api_key = api_key
        self.sender_email = sender_email
        self.endpoint = "https://api.mailersend.com/v1/email"

    def send_email(self, recipient_email, recipient_name, template_id, attachment_path=None, retries=3, backoff_factor=2):
        logger.info(f" This is the template id {template_id}")
        payload = {
            "from": {"email": self.sender_email, "name": "Third Wave Cafe"},
            "to": [{"email": recipient_email}],
            "subject": "Your Birthday Voucher",
            "template_id": template_id,
            "variables": [
                {
                    "email": recipient_email,
                    "substitutions": [
                        {"var": "username", "value": recipient_name},
                    ]
                }
            ]
        }

        if attachment_path:
            if os.path.exists(attachment_path):
                try:
                    with open(attachment_path, 'rb') as file:
                        file_content = file.read()
                        encoded_content = base64.b64encode(file_content).decode('utf-8')
                    
                    # Add the attachment to the payload
                    payload["attachments"] = [
                        {
                            "filename": os.path.basename(attachment_path),
                            "content": encoded_content,
                            "disposition": "attachment"
                        }
                    ]
                    logger.info(f"Attached file: {os.path.basename(attachment_path)}")
                except Exception as e:
                    logger.error(f"Failed to read and encode attachment: {e}")
                    return False
            else:
                logger.error(f"Attachment path '{attachment_path}' does not exist.")
                return False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Attempt {attempt}: Sending email to {recipient_email}")

                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=payload  # Send payload as JSON
                )

                if 200 <= response.status_code < 300:
                    logger.info(f"Email sent successfully to {recipient_email}")
                    return True
                else:
                    logger.error(f"Failed to send email on attempt {attempt}: {response.status_code} - {response.text}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Exception on attempt {attempt}: {e}")

            # Exponential backoff
            sleep_time = backoff_factor ** attempt
            logger.info(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)

        logger.error(f"All {retries} attempts to send email to {recipient_email} have failed.")
        return False

if __name__ == "__main__":
    api_key = os.getenv("MAILERSEND_API_KEY")
    sender = os.getenv("MAILERSEND_SENDER")
    template_id = os.getenv("MAILERSEND_NEXT_YEAR_2WEEKS_ID")
    recipient = os.getenv("RECIPIENT_EMAIL")

    if not all([api_key, sender, template_id, recipient]):
        logger.error("Missing environment variables. Please check your .env file.")
        exit(1)

    client = MailerSendClient(api_key, sender)
    pdf_path = "test.pdf" 

    success = client.send_email(recipient, "John Doe", template_id, attachment_path=pdf_path)
    if success:
        logger.info("Email process completed successfully.")
    else:
        logger.error("Email process failed.")
