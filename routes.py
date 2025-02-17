from flask import Blueprint, request, jsonify
import datetime
import logging
import os

from config import (
    WEBHOOK_SECRET_TOKEN,
    MAILERSEND_WELCOME_TEMPLATE_ID,
    CELLCAST_WELCOME_TEMPLATE_ID,
    MAIN_TABLE,
    MAILERSEND_API_KEY,
    MAILERSEND_SENDER,
    CELLCAST_API_KEY,
    CELLCAST_SENDER_ID,
    GOOGLE_SHEETS_CREDENTIALS,
    GOOGLE_SHEETS_ID,
    GOOGLE_SHEETS_WORKSHEET
)
from db import get_db_connection
from services import get_next_voucher_code
from send_email import MailerSendClient
from send_sms import CellCastClient
from create_voucher_pdf import generate_voucher_pdf

# Import the Google Sheets client
from google_sheets_client import GoogleSheetsClient

logger = logging.getLogger(__name__)
bp = Blueprint('routes', __name__)

# Initialize external clients.
mailer_client = MailerSendClient(
    api_key=MAILERSEND_API_KEY,
    sender_email=MAILERSEND_SENDER
)
cellcast_client = CellCastClient(
    app_key=CELLCAST_API_KEY,
    sender_id=CELLCAST_SENDER_ID
)
# Initialize Google Sheets client.
sheets_client = GoogleSheetsClient(
    credentials_json=GOOGLE_SHEETS_CREDENTIALS,
    spreadsheet_id=GOOGLE_SHEETS_ID,
    worksheet_name=GOOGLE_SHEETS_WORKSHEET
)

@bp.route('/signup', methods=['POST'])
def signup():
    """
    Endpoint to register a new user.
    Expects a JSON payload with: name, email, phone_number, birth_day, birth_month.
    After inserting the new record, sends a welcome email (with a PDF voucher)
    and SMS, then updates the database with the success flags.
    Also, appends the signup data to a Google Sheets document.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone_number = data.get("phone_number", "").strip()
    birth_day = data.get("birth_day")
    birth_month = data.get("birth_month")  # Ensure the client sends "birth_month"

    if not (name and email and phone_number and birth_day and birth_month):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    # Establish database connection.
    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    # Check for duplicate email.
    query = f"SELECT id FROM {MAIN_TABLE} WHERE email = %s"
    cursor.execute(query, (email,))
    if cursor.fetchone():
        cursor.close()
        db_conn.close()
        return jsonify({"status": "error", "message": "Duplicate email"}), 400

    # Generate a new voucher code.
    voucher_code = get_next_voucher_code()
    signup_date = datetime.date.today()  # Full signup date

    # Insert new user record.
    insert_query = f"""
    INSERT INTO {MAIN_TABLE} 
        (name, birth_day, birth_month, signup_date, email, phone_number, email_sent, sms_sent, voucher_code)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (name, birth_day, birth_month, signup_date, email, phone_number, 0, 0, voucher_code))
    user_id = cursor.lastrowid
    db_conn.commit()

    # Append data to Google Sheets.
    row_data = [
        name,
        birth_day,
        birth_month,
        email,
        phone_number,
        signup_date.strftime("%Y-%m-%d"),
        voucher_code
    ]
    sheets_result = sheets_client.append_row(row_data)
    if not sheets_result:
        logger.error("Failed to append signup data to Google Sheets.")

    # Generate the voucher PDF.
    pdf_path = generate_voucher_pdf(name, voucher_code)
    email_success = False
    sms_success = False

    if pdf_path:
        email_success = mailer_client.send_email(email, name, MAILERSEND_WELCOME_TEMPLATE_ID, pdf_path)
        try:
            os.remove(pdf_path)
        except Exception as e:
            logger.warning(f"Could not delete PDF {pdf_path}: {e}")
    else:
        logger.error("Failed to generate voucher PDF.")

    # Prepare and send SMS.
    image_url = f"http://209.38.84.84/images/voucher_{voucher_code}.jpg"
    recipient_data = [{
        "number": phone_number,
        "fname": name,
        "custom_value_1": image_url
    }]
    sms_success = cellcast_client.send_sms_template(CELLCAST_WELCOME_TEMPLATE_ID, recipient_data)

    # Update the user record with the outcome of the welcome email and SMS.
    update_query = f"UPDATE {MAIN_TABLE} SET email_sent = %s, sms_sent = %s WHERE id = %s"
    cursor.execute(update_query, (1 if email_success else 0, 1 if sms_success else 0, user_id))
    db_conn.commit()

    cursor.close()
    db_conn.close()

    return jsonify({"status": "success", "email": email_success, "sms": sms_success}), 200

@bp.route('/daily-check', methods=['GET'])
def daily_check():
    """
    Daily endpoint to:
      - Update voucher codes 8 days after the last birthday.
      - Check if a reminder (2 weeks or 1 month) is due for each user.
      - Send out the reminder email and SMS using appropriate templates.
    Requires the proper Authorization header.
    """
    auth_token = request.headers.get('Authorization')
    if not auth_token or auth_token != WEBHOOK_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized."}), 401

    today = datetime.date.today()
    logger.info(f"Starting daily check for {today}")
    db_conn = get_db_connection()
    cursor = db_conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {MAIN_TABLE}")
    users = cursor.fetchall()

    results = []

    for user in users:
        user_id = user['id']
        name = user['name']
        email = user['email']
        phone_number = user['phone_number']
        voucher_code = user['voucher_code']
        birth_day = int(user['birth_day'])
        birth_month = int(user['birth_month'])
        signup_date = user['signup_date']

        # Compute the birthday for the current year.
        try:
            birthday_date = datetime.date(today.year, birth_month, birth_day)
        except ValueError:
            logger.error(f"Invalid birthday for user {user_id}")
            continue

        # Determine the user's first birthday after signup.
        first_birthday = datetime.date(signup_date.year, birth_month, birth_day)
        if first_birthday < signup_date:
            first_birthday = datetime.date(signup_date.year + 1, birth_month, birth_day)
        first_birthday_passed = today >= first_birthday

        # Voucher Update Logic (8 days after last birthday)
        if today >= birthday_date:
            last_birthday = birthday_date
        else:
            last_birthday = datetime.date(today.year - 1, birth_month, birth_day)
        voucher_gen_date = last_birthday + datetime.timedelta(days=8)
        voucher_updated = False
        if today == voucher_gen_date and today > last_birthday:
            new_voucher_code = get_next_voucher_code()
            update_query = f"UPDATE {MAIN_TABLE} SET voucher_code = %s WHERE id = %s"
            cursor.execute(update_query, (new_voucher_code, user_id))
            db_conn.commit()
            logger.info(f"User {user_id} voucher updated from {voucher_code} to {new_voucher_code}")
            voucher_code = new_voucher_code
            voucher_updated = True

        # Reminder Logic for Birthday Reminders
        if today >= birthday_date:
            upcoming_birthday = datetime.date(today.year + 1, birth_month, birth_day)
        else:
            upcoming_birthday = birthday_date

        one_month_before = upcoming_birthday - datetime.timedelta(days=30)
        two_weeks_before = upcoming_birthday - datetime.timedelta(days=14)

        reminder_results = {}
        image_url = f"http://209.38.84.84/images/voucher_{voucher_code}.jpg"
        recipient_data = [{
            "number": phone_number,
            "fname": name,
            "custom_value_1": image_url
        }]

        if today == two_weeks_before:
            template_key = "1ST_2WEEKS" if not first_birthday_passed else "2ND_2WEEKS"
            email_template_id = os.getenv(f"MAILERSEND_{template_key}_ID", "")
            sms_template_id = os.getenv(f"CELLCAST_{template_key}_ID", "")
            logger.info(f"Sending two-week reminder for user {user_id} using {template_key}")
            email_reminder_success = mailer_client.send_email(email, name, email_template_id, None)
            sms_reminder_success = cellcast_client.send_sms_template(sms_template_id, recipient_data)
            reminder_results['two_weeks'] = {"email": email_reminder_success, "sms": sms_reminder_success}

        if today == one_month_before and first_birthday_passed:
            template_key = "1MONTH"
            email_template_id = os.getenv(f"MAILERSEND_{template_key}_ID", "")
            sms_template_id = os.getenv(f"CELLCAST_{template_key}_ID", "")
            logger.info(f"Sending one-month reminder for user {user_id} using {template_key}")
            email_reminder_success = mailer_client.send_email(email, name, email_template_id, None)
            sms_reminder_success = cellcast_client.send_sms_template(sms_template_id, recipient_data)
            reminder_results['one_month'] = {"email": email_reminder_success, "sms": sms_reminder_success}

        results.append({
            "user_id": user_id,
            "voucher_updated": voucher_updated,
            "reminders": reminder_results
        })

    cursor.close()
    db_conn.close()
    logger.info("Daily check completed.")
    return jsonify({"status": "success", "results": results}), 200
