# send_sms_template.py

import os
import time
import requests
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# Add the handler to the logger if not already added
if not logger.handlers:
    logger.addHandler(ch)


class CellCastClient:
    def __init__(
        self,
        app_key: str,
        sender_id: Optional[str] = None,
        source: Optional[str] = None,
        custom_string: Optional[str] = None
    ):
        """
        Initializes the CellCastClient with necessary configurations.

        Parameters:
            - app_key (str): Your CellCast APPKEY.
            - sender_id (str, optional): Your approved Sender ID (e.g., "TWCafe").
            - source (str, optional): Source identifier (e.g., "Zoho").
            - custom_string (str, optional): Custom string identifier (e.g., "Zoho").
        """
        self.app_key = app_key
        self.sender_id = sender_id
        self.source = source
        self.custom_string = custom_string
        # Endpoint updated for sending SMS via template
        self.endpoint = "https://cellcast.com.au/api/v3/send-sms-template"

    def send_sms_template(
        self,
        template_id: str,
        numbers: List[Dict[str, Any]],
        schedule_time: Optional[str] = None,
        delay: Optional[int] = None,
        retries: int = 3,
        backoff_factor: int = 2
    ) -> bool:
        """
        Sends an SMS using a predefined template via the CellCast API.

        Parameters:
            - template_id (str): Template ID from the get-template API.
            - numbers (List[Dict[str, Any]]): List of dictionaries for each recipient.
              Each dictionary should include at least the key "number". You can also include
              merge fields like "fname", "lname", etc., as required by your template.
              Example:
                  [
                      {
                          "number": "61413123456",
                          "fname": "John",
                          "custom_value_1 = "TWC_123"
                      },
                      # More recipient dictionaries...
                  ]
            - schedule_time (str, optional): Schedule time in "Y-m-d H:i:s" format.
            - delay (int, optional): Delay in minutes (1 to 1440).
            - retries (int, optional): Number of retry attempts.
            - backoff_factor (int, optional): Factor for exponential backoff.

        Returns:
            bool: True if the SMS was sent successfully, False otherwise.
        """
        headers = {
            "APPKEY": self.app_key,
            "Content-Type": "application/json"
        }

        payload = {
            "template_id": template_id,
            "numbers": numbers
        }

        if self.sender_id:
            payload["from"] = self.sender_id
        if self.source:
            payload["source"] = self.source
        if self.custom_string:
            payload["custom_string"] = self.custom_string
        if schedule_time:
            payload["schedule_time"] = schedule_time
        if delay:
            payload["delay"] = delay

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Attempt {attempt}: Sending template SMS to recipients.")
                response = requests.post(self.endpoint, headers=headers, json=payload)

                logger.info(f"Response Code: {response.status_code}")
                logger.info(f"Response Text: {response.text}")

                if response.status_code == 200:
                    response_json = response.json()
                    meta = response_json.get("meta", {})
                    code = meta.get("code")
                    msg = response_json.get("msg", "")

                    if code == 200:
                        logger.info("Template SMS sent successfully!")
                        return True
                    else:
                        logger.error(f"Failed to send Template SMS: {msg} (Code: {code})")
                else:
                    logger.error(f"Failed to send Template SMS: HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Exception on attempt {attempt}: {e}")

            # Exponential backoff before retrying
            sleep_time = backoff_factor ** attempt
            logger.info(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)

        logger.error(f"All {retries} attempts to send the template SMS have failed.")
        return False


if __name__ == "__main__":
    CELLCAST_APPKEY = os.getenv("CELLCAST_API_KEY", "")
    TEMPLATE_ID = os.getenv("CELLCAST_1ST_2WEEKS_ID", "")
    RECIPIENTS = [
        {
            "number": "61423325333",
            "fname": "John",
            "custom_value_1": "http://209.38.84.84/images/voucher_ABC123.jpg",
        },
    ]
    SENDER_ID = os.getenv("CELLCAST_SENDER_ID", "DefaultSender") 

    # Optional parameters
    SOURCE = "Zoho"
    CUSTOM_STRING = "Zoho"
    SCHEDULE_TIME = None
    DELAY = None

    # Initialize the CellCast Client with template parameters
    cellcast_client = CellCastClient(
        app_key=CELLCAST_APPKEY,
        sender_id=SENDER_ID,
        source=SOURCE,
        custom_string=CUSTOM_STRING
    )

    # Send Template SMS
    success = cellcast_client.send_sms_template(
        template_id=TEMPLATE_ID,
        numbers=RECIPIENTS,
        schedule_time=SCHEDULE_TIME,
        delay=DELAY
    )

    if success:
        logger.info("Template SMS process completed successfully.")
    else:
        logger.error("Template SMS process failed.")
