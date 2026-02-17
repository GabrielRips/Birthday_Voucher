# webhook_app.py

from flask import Flask, request, jsonify
import logging
import os
from send_email import MailerSendClient
from send_sms import CellCastClient  # This module now has send_sms_template method
from dotenv import load_dotenv
import re
import random
import string
from create_voucher_pdf import generate_voucher_pdf  # Assuming you have this module
from database import Database
from scheduler import VoucherScheduler
from google_sheets import GoogleSheetsClient

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

# Initialize Database
db = Database()
if not db.connect():
    logger.error("Failed to connect to MySQL database. Please check your database configuration.")
    exit(1)

# Create tables if they don't exist
db.create_tables()

# Initialize and start scheduler
scheduler = VoucherScheduler(db, mailer_client, cellcast_client)
scheduler.start()

# Initialize Google Sheets client
logger.info("Initializing Google Sheets client...")
google_sheets_client = GoogleSheetsClient()
if google_sheets_client.worksheet is None:
    logger.warning("⚠️  Google Sheets client FAILED to initialize. Google Sheets writes will be skipped.")
    logger.warning("   Check your .env file for GOOGLE_SHEETS_CREDENTIALS_FILE and GOOGLE_SHEETS_SPREADSHEET_ID")
else:
    logger.info("✅ Google Sheets client initialized successfully!")

def is_valid_email(email):
    regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.match(regex, email)

def is_valid_phone(phone):
    return re.match(r'^(\+?61\d{9}|04\d{8})$', phone)

def generate_voucher_code():
    """Generate a unique voucher code in format xxxxxxx (7 digits)"""
    max_attempts = 100
    for _ in range(max_attempts):
        # Generate 7 random digits
        voucher_code = ''.join(random.choices(string.digits, k=7))
        
        # Check if code already exists in database
        if not db.voucher_code_exists(voucher_code):
            return voucher_code
    
    # Fallback: use timestamp-based code if all random attempts fail
    import time
    timestamp = str(int(time.time()))[-7:]  # Last 7 digits of timestamp
    return timestamp

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
        name = data.get("Name", "").strip()
        email = data.get("eMail", "").strip()
        phone = data.get("Phone", "").strip()
        birthday = data.get("Birthday_DAY")  # Day of month (1-31)
        birth_month = data.get("Birthday_MONTH")  # Month (1-12)
        voucher_code = data.get("voucherCode", "").strip()
        
        # Validate and convert birthday and birth_month to integers
        try:
            if birthday is not None:
                birthday = int(birthday)
                if birthday < 1 or birthday > 31:
                    logger.warning(f"Invalid birthday value: {birthday}. Must be between 1-31.")
                    birthday = None
        except (ValueError, TypeError):
            logger.warning(f"Invalid birthday format: {data.get('Birthday_DAY')}")
            birthday = None
        
        try:
            if birth_month is not None:
                birth_month = int(birth_month)
                if birth_month < 1 or birth_month > 12:
                    logger.warning(f"Invalid birth_month value: {birth_month}. Must be between 1-12.")
                    birth_month = None
        except (ValueError, TypeError):
            logger.warning(f"Invalid birth_month format: {data.get('Birthday_MONTH')}")
            birth_month = None

        # Use default email template (MailerSend)
        email_template_id = os.getenv("MAILERSEND_DEFAULT_TEMPLATE_ID")

        logger.info(f"Received data - Name: '{name}', Email: '{email}', Phone: '{phone}', Birthday: '{birthday}', Birth Month: '{birth_month}', Voucher: '{voucher_code}'")

        # Validate required fields
        if not name:
            logger.error("Name is required.")
            return jsonify({"status": "error", "message": "Name is required."}), 400

        # Generate voucher code if not provided
        if not voucher_code:
            voucher_code = generate_voucher_code()
            logger.info(f"Generated new voucher code: {voucher_code}")
        else:
            # Check if provided voucher code already exists
            if db.voucher_code_exists(voucher_code):
                logger.error(f"Voucher code already exists: {voucher_code}")
                return jsonify({"status": "error", "message": "Voucher code already exists."}), 400

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

        # Store data in MySQL database
        try:
            voucher_id = db.insert_voucher(
                name=name,
                phone=phone if phone and phone_valid else None,
                email=email if email and email_valid else None,
                birthday=birthday,
                birth_month=birth_month,
                voucher_code=voucher_code
            )
            if voucher_id:
                logger.info(f"Successfully stored voucher in database with ID: {voucher_id}")
            else:
                logger.error("Failed to store voucher in database")
                return jsonify({"status": "error", "message": "Failed to store voucher in database."}), 500
        except Exception as e:
            logger.exception(f"Error storing voucher in database: {e}")
            return jsonify({"status": "error", "message": "Database error occurred."}), 500

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
            # Use default SMS template (CellCast)
            sms_template_id = os.getenv("CELLCAST_TEMPLATE_ID")

            image_url = f"http://170.64.230.163/voucher/voucher_{voucher_code}.jpg"
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

        # Write entry to Google Sheets
        try:
            google_sheets_client.write_entry(
                name=name,
                birthday=birthday,
                birth_month=birth_month,
                email=email if email and email_valid else None,
                phone=phone if phone and phone_valid else None,
                email_success=email_success,
                sms_success=sms_success
            )
        except Exception as e:
            logger.exception(f"Failed to write to Google Sheets: {e}")
            # Don't fail the request if Google Sheets write fails

        # Return a detailed JSON response
        result = {
            "status": "success",
            "voucher_code": voucher_code,
            "voucher_id": voucher_id,
            "email": email_success,
            "sms": sms_success
        }
        logger.info(result)
        return jsonify(result), 200

    except Exception as e:
        logger.exception("An unexpected error occurred in birthday_webhook.")
        return jsonify({"status": "error", "message": "Internal server error."}), 500

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()
        db.disconnect()
