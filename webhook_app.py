# webhook_app.py

from flask import Flask, request, jsonify
import logging
import os
from send_email import MailerSendClient
from send_sms import CellCastClient  # This module now has send_sms_template method
from dotenv import load_dotenv
import re
from create_voucher_pdf import generate_voucher_pdf  # Assuming you have this module

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize Logger
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for detailed logs
logger = logging.getLogger(__name__)

# Set up RotatingFileHandler
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('app.log', maxBytes=1000000, backupCount=5)
handler.setLevel(logging.DEBUG)  # Set to DEBUG to capture detailed logs
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Load MailerSend Credentials
mailersend_api_key = os.getenv("MAILERSEND_API_KEY")
mailersend_sender = os.getenv("MAILERSEND_SENDER")

logger.info(f"MAILERSEND_API_KEY: {'Loaded' if mailersend_api_key else 'Missing'}")
logger.info(f"MAILERSEND_SENDER: {mailersend_sender}")

if not mailersend_api_key or not mailersend_sender:
    logger.error("Missing MailerSend credentials. Please check .env file.")
    exit(1)

mailer_client = MailerSendClient(
    api_key=mailersend_api_key,
    sender_email=mailersend_sender,
)

# Initialize CellCast Client (SMS)
cellcast_api_key = os.getenv("CELLCAST_API_KEY")
cellcast_sender_id = os.getenv("CELLCAST_SENDER_ID")  # Optional
cellcast_client = CellCastClient(app_key=cellcast_api_key, sender_id=cellcast_sender_id)

WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")

def is_valid_email(email):
    regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.match(regex, email)

def is_valid_phone(phone):
    return re.match(r'^\+?61\d{9}$', phone)

@app.route('/birthday-webhook', methods=['POST'])
def birthday_webhook():
    try:
        auth_token = request.headers.get('Authorization')
        if not auth_token or auth_token != WEBHOOK_SECRET_TOKEN:
            logger.warning("Unauthorized access attempt.")
            return jsonify({"status": "error", "message": "Unauthorized."}), 401

        data = request.get_json()
        if not data:
            logger.error("No JSON received")
            return jsonify({"status": "error", "message": "No JSON received"}), 400

        # Extract fields from the payload (default to empty string if missing)
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        voucher_code = data.get("voucherCode", "").strip()
        template_type = data.get("templateType", "default").strip()

        # Mapping for email templates (MailerSend)
        email_template_mapping = {
            "TEMPLATE_1ST_2WEEKS": os.getenv("MAILERSEND_1ST_2WEEKS_ID"),
            "TEMPLATE_1MONTH": os.getenv("MAILERSEND_NEXT_YEAR_1MONTH_ID"),
            "TEMPLATE_2ND_2WEEKS": os.getenv("MAILERSEND_NEXT_YEAR_2WEEKS_ID")
        }
        email_template_id = email_template_mapping.get(
            template_type, 
            os.getenv("MAILERSEND_DEFAULT_TEMPLATE_ID")
        )

        logger.info(f"Received data - Name: '{name}', Email: '{email}', Phone: '{phone}', Voucher: '{voucher_code}'")

        # Log warnings if any fields are missing but do not abort
        if not name:
            logger.warning("Name is missing.")
        if not email:
            logger.warning("Email is missing.")
        if not phone:
            logger.warning("Phone is missing.")
        if not voucher_code:
            logger.info("Voucher code is missing. A new one will be generated.")

        # Validate email and phone formats separately
        email_valid = True
        phone_valid = True

        if email and not is_valid_email(email):
            logger.error(f"Invalid email format: {email}")
            email_valid = False

        if phone and not is_valid_phone(phone):
            logger.error(f"Invalid phone format: {phone}")
            phone_valid = False

        # If both email and phone are provided but invalid, then nothing can be sent.
        if email and phone and not (email_valid or phone_valid):
            logger.error("Both email and phone formats are invalid.")
            return jsonify({"status": "error", "message": "Both email and phone formats are invalid."}), 400

        # Generate voucher code if not provided
        if not voucher_code:
            logger.error("Missing voucher code. Aborting.")
            return jsonify({"status": "error", "message": "Missing voucher code."}), 400

        # Initialize success flags
        email_success = False
        sms_success = False

        # Only generate the PDF voucher and send email if email is provided and valid
        if email and email_valid:
            pdf_path = generate_voucher_pdf(name, voucher_code)
            if not pdf_path:
                logger.error("Failed to generate PDF voucher.")
            else:
                logger.info(f"Generated PDF voucher at: {pdf_path}")
                # Send Email with PDF attachment
                logger.info(f"Preparing to send email to {email} with attachment {pdf_path}")
                logger.info(f"Email Template id: {email_template_id}")
                email_success = mailer_client.send_email(email, name, email_template_id, pdf_path)
                if email_success:
                    logger.info(f"Email sent successfully to {email}")
                else:
                    logger.error(f"Failed to send email to {email}")
                try:
                    os.remove(pdf_path)
                    logger.info(f"Deleted temporary PDF file: {pdf_path}")
                except Exception as e:
                    logger.warning(f"Could not delete PDF file {pdf_path}: {e}")
        else:
            logger.info("Skipping email sending due to missing or invalid email.")

        # --- SMS Sending using Template ---
        # Only send SMS if phone is provided and valid.
        if phone and phone_valid:
            # Map incoming template type to the corresponding CellCast SMS template id.
            sms_template_mapping = {
                "TEMPLATE_1ST_2WEEKS": os.getenv("CELLCAST_1ST_2WEEKS_ID"),
                "TEMPLATE_1MONTH": os.getenv("CELLCAST_NEXT_YEAR_1MONTH_ID"),
                "TEMPLATE_2ND_2WEEKS": os.getenv("CELLCAST_NEXT_YEAR_2WEEKS_ID")
            }
            sms_template_id = sms_template_mapping.get(template_type, os.getenv("CELLCAST_TEMPLATE_ID"))

            image_url = f"http://209.38.84.84/images/voucher_{voucher_code}.jpg"
            # Build recipient data for the SMS template call.
            # Adjust merge fields as required by your SMS template.
            recipient_data = [{
                "number": phone,
                "fname": name,
                "custom_value_1": image_url
            }]

            logger.info(f"Sending SMS using template id: {sms_template_id} to {phone}")
            sms_success = cellcast_client.send_sms_template(
                template_id=sms_template_id,
                numbers=recipient_data
            )
            if sms_success:
                logger.info(f"SMS sent successfully to {phone}")
            else:
                logger.error(f"Failed to send SMS to {phone}")
        else:
            logger.info("Skipping SMS sending due to missing or invalid phone.")

        # Return a detailed JSON response
        result = {
            "status": "success",
            "email": email_success,
            "sms": sms_success
        }
        logger.info(result)
        return jsonify(result), 200

    except Exception as e:
        logger.exception("An unexpected error occurred in birthday_webhook.")
        return jsonify({"status": "error", "message": "Internal server error."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
