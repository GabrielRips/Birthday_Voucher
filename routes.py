from flask import Blueprint, request, jsonify
import datetime
import logging
import os

from config import (
    WEBHOOK_SECRET_TOKEN,
    MAILERSEND_WELCOME_TEMPLATE_ID,
    CELLCAST_WELCOME_TEMPLATE_ID,
    MAIN_TABLE,
    MANYCHAT_TABLE,
    CAMPAIGNS_CONFIG_TABLE,
    VOUCHER_IMAGE_BASE_URL,
    MAILERSEND_API_KEY,
    MAILERSEND_SENDER,
    CELLCAST_API_KEY,
    CELLCAST_SENDER_ID,
    GOOGLE_SHEETS_CREDENTIALS,
    GOOGLE_SHEETS_ID,
    GOOGLE_SHEETS_WORKSHEET
)
from db import get_db_connection
from services import get_next_voucher_code, get_next_manychat_voucher_code, get_campaign_config
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

@bp.route('/manychat-webhook', methods=['POST'])
def manychat_webhook():
    """
    Endpoint to receive data from ManyChat webhook.
    Expects a JSON payload with: name, phone, email, city, campaign.
    Optionally accepts: email_template_id, sms_template_id for campaign-specific templates.
    Generates a unique voucher code and issue date, stores the data in the ManyChat table,
    creates a voucher PDF with issue date, and sends it via email and SMS.
    Supports multiple campaigns - same email can be used in different campaigns.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400

    # ManyChat may send data in different formats, handle both direct fields and nested structures
    name = data.get("name") or data.get("sender_name", "").strip()
    phone = data.get("phone") or data.get("phone_number", "").strip()
    email = data.get("email", "").strip()
    city = data.get("city", "").strip()
    campaign = data.get("campaign", "").strip()

    if not (name and phone and email and campaign):
        return jsonify({
            "status": "error", 
            "message": "Missing required fields: name, phone, email, and campaign are required"
        }), 400

    # Fetch campaign configuration from database
    campaign_config = get_campaign_config(campaign)
    
    if not campaign_config:
        return jsonify({
            "status": "error",
            "message": f"Campaign '{campaign}' not found or not active. Please configure the campaign first."
        }), 400

    # Use campaign defaults, but allow override from request
    email_template_id = data.get("email_template_id", "").strip() or campaign_config.get('email_template_id') or MAILERSEND_WELCOME_TEMPLATE_ID
    sms_template_id = data.get("sms_template_id", "").strip() or campaign_config.get('sms_template_id') or CELLCAST_WELCOME_TEMPLATE_ID
    voucher_image_path = campaign_config.get('voucher_image_path')
    # Use global image_base_url from config (same for all campaigns)
    # Campaign-specific image_base_url can override if needed, but typically not necessary
    image_base_url = campaign_config.get('image_base_url') or VOUCHER_IMAGE_BASE_URL

    # Establish database connection
    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    try:
        # Check for duplicate email within the same campaign (not globally)
        query = f"SELECT id FROM {MANYCHAT_TABLE} WHERE campaign = %s AND email = %s"
        cursor.execute(query, (campaign, email))
        if cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({
                "status": "error", 
                "message": f"Duplicate email for campaign '{campaign}'. Same email can be used in different campaigns."
            }), 400

        # Generate unique voucher code and issue date
        voucher_code = get_next_manychat_voucher_code()
        issue_date = datetime.date.today()

        # Insert new record into ManyChat table with campaign support
        insert_query = f"""
        INSERT INTO {MANYCHAT_TABLE} 
            (campaign, name, phone, email, city, voucher_code, issue_date, email_template_id, sms_template_id, email_sent, sms_sent)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            campaign, name, phone, email, city, voucher_code, issue_date, 
            email_template_id, sms_template_id, 0, 0
        ))
        record_id = cursor.lastrowid
        db_conn.commit()

        # Generate the voucher PDF with campaign-specific image and issue date
        pdf_path = generate_voucher_pdf(
            name, 
            voucher_code, 
            output_dir='vouchers', 
            issue_date=issue_date,
            voucher_image_path=voucher_image_path
        )
        email_success = False
        sms_success = False

        if pdf_path:
            email_success = mailer_client.send_email(email, name, email_template_id, pdf_path)
            try:
                os.remove(pdf_path)
            except Exception as e:
                logger.warning(f"Could not delete PDF {pdf_path}: {e}")
        else:
            logger.error("Failed to generate voucher PDF.")

        # Prepare and send SMS with campaign-specific image URL
        # Ensure image_base_url ends with / if not empty
        if image_base_url and not image_base_url.endswith('/'):
            image_base_url += '/'
        image_url = f"{image_base_url}voucher_{voucher_code}.jpg"
        recipient_data = [{
            "number": phone,
            "fname": name,
            "custom_value_1": image_url
        }]
        sms_success = cellcast_client.send_sms_template(sms_template_id, recipient_data)

        # Update the record with the outcome of the email and SMS
        update_query = f"UPDATE {MANYCHAT_TABLE} SET email_sent = %s, sms_sent = %s WHERE id = %s"
        cursor.execute(update_query, (1 if email_success else 0, 1 if sms_success else 0, record_id))
        db_conn.commit()

        cursor.close()
        db_conn.close()

        return jsonify({
            "status": "success",
            "campaign": campaign,
            "voucher_code": voucher_code,
            "issue_date": issue_date.strftime("%Y-%m-%d"),
            "email": email_success,
            "sms": sms_success
        }), 200

    except Exception as e:
        logger.error(f"Error processing ManyChat webhook: {e}")
        if db_conn:
            db_conn.rollback()
            cursor.close()
            db_conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/manychat-vouchers', methods=['GET'])
def get_manychat_vouchers():
    """
    Endpoint to query ManyChat vouchers by campaign.
    Requires Authorization header.
    Query parameters:
    - campaign (required): Filter by campaign name
    - email (optional): Filter by specific email
    - limit (optional): Limit number of results (default: 100)
    """
    # Require authentication
    auth_token = request.headers.get('Authorization')
    if not auth_token or auth_token != WEBHOOK_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized."}), 401
    
    campaign = request.args.get('campaign', '').strip()
    email = request.args.get('email', '').strip()
    limit = request.args.get('limit', '100')
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 100
    
    if not campaign:
        return jsonify({"status": "error", "message": "campaign parameter is required"}), 400
    
    db_conn = get_db_connection()
    cursor = db_conn.cursor(dictionary=True)
    
    try:
        if email:
            query = f"""
            SELECT id, campaign, name, phone, email, city, voucher_code, issue_date, 
                   email_template_id, sms_template_id, email_sent, sms_sent, created_at
            FROM {MANYCHAT_TABLE}
            WHERE campaign = %s AND email = %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            cursor.execute(query, (campaign, email, limit))
        else:
            query = f"""
            SELECT id, campaign, name, phone, email, city, voucher_code, issue_date, 
                   email_template_id, sms_template_id, email_sent, sms_sent, created_at
            FROM {MANYCHAT_TABLE}
            WHERE campaign = %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            cursor.execute(query, (campaign, limit))
        
        vouchers = cursor.fetchall()
        
        # Convert date objects to strings for JSON serialization
        for voucher in vouchers:
            if voucher.get('issue_date'):
                voucher['issue_date'] = voucher['issue_date'].strftime("%Y-%m-%d") if hasattr(voucher['issue_date'], 'strftime') else str(voucher['issue_date'])
            if voucher.get('created_at'):
                voucher['created_at'] = voucher['created_at'].isoformat() if hasattr(voucher['created_at'], 'isoformat') else str(voucher['created_at'])
        
        cursor.close()
        db_conn.close()
        
        return jsonify({
            "status": "success",
            "campaign": campaign,
            "count": len(vouchers),
            "vouchers": vouchers
        }), 200
        
    except Exception as e:
        logger.error(f"Error querying ManyChat vouchers: {e}")
        if db_conn:
            cursor.close()
            db_conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/manychat-campaigns', methods=['GET'])
def get_campaigns():
    """
    Endpoint to get list of all campaigns and their statistics.
    Requires Authorization header.
    """
    # Require authentication
    auth_token = request.headers.get('Authorization')
    if not auth_token or auth_token != WEBHOOK_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized."}), 401
    
    db_conn = get_db_connection()
    cursor = db_conn.cursor(dictionary=True)
    
    try:
        query = f"""
        SELECT 
            campaign,
            COUNT(*) as total_vouchers,
            SUM(email_sent) as emails_sent,
            SUM(sms_sent) as sms_sent,
            MIN(created_at) as first_voucher,
            MAX(created_at) as last_voucher
        FROM {MANYCHAT_TABLE}
        GROUP BY campaign
        ORDER BY campaign ASC
        """
        cursor.execute(query)
        campaigns = cursor.fetchall()
        
        # Convert datetime objects to strings
        for campaign in campaigns:
            if campaign.get('first_voucher'):
                campaign['first_voucher'] = campaign['first_voucher'].isoformat() if hasattr(campaign['first_voucher'], 'isoformat') else str(campaign['first_voucher'])
            if campaign.get('last_voucher'):
                campaign['last_voucher'] = campaign['last_voucher'].isoformat() if hasattr(campaign['last_voucher'], 'isoformat') else str(campaign['last_voucher'])
        
        cursor.close()
        db_conn.close()
        
        return jsonify({
            "status": "success",
            "count": len(campaigns),
            "campaigns": campaigns
        }), 200
        
    except Exception as e:
        logger.error(f"Error querying campaigns: {e}")
        if db_conn:
            cursor.close()
            db_conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/campaigns-config', methods=['GET'])
def get_campaign_config_endpoint():
    """
    Get campaign configuration(s).
    Requires Authorization header.
    Query parameters:
    - campaign (optional): Get specific campaign config, or all if not provided
    """
    # Require authentication
    auth_token = request.headers.get('Authorization')
    if not auth_token or auth_token != WEBHOOK_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized."}), 401
    
    campaign = request.args.get('campaign', '').strip()
    db_conn = get_db_connection()
    cursor = db_conn.cursor(dictionary=True)
    
    try:
        if campaign:
            query = f"SELECT * FROM {CAMPAIGNS_CONFIG_TABLE} WHERE campaign = %s"
            cursor.execute(query, (campaign,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                db_conn.close()
                return jsonify({"status": "error", "message": f"Campaign '{campaign}' not found"}), 404
            
            # Convert datetime to string
            if result.get('created_at'):
                result['created_at'] = result['created_at'].isoformat() if hasattr(result['created_at'], 'isoformat') else str(result['created_at'])
            if result.get('updated_at'):
                result['updated_at'] = result['updated_at'].isoformat() if hasattr(result['updated_at'], 'isoformat') else str(result['updated_at'])
            
            cursor.close()
            db_conn.close()
            return jsonify({"status": "success", "config": result}), 200
        else:
            query = f"SELECT * FROM {CAMPAIGNS_CONFIG_TABLE} ORDER BY campaign ASC"
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Convert datetime to string
            for result in results:
                if result.get('created_at'):
                    result['created_at'] = result['created_at'].isoformat() if hasattr(result['created_at'], 'isoformat') else str(result['created_at'])
                if result.get('updated_at'):
                    result['updated_at'] = result['updated_at'].isoformat() if hasattr(result['updated_at'], 'isoformat') else str(result['updated_at'])
            
            cursor.close()
            db_conn.close()
            return jsonify({"status": "success", "count": len(results), "configs": results}), 200
            
    except Exception as e:
        logger.error(f"Error fetching campaign config: {e}")
        if db_conn:
            cursor.close()
            db_conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/campaigns-config', methods=['POST'])
def create_campaign_config():
    """
    Create or update a campaign configuration.
    Requires Authorization header.
    Request body should include:
    - campaign (required): Campaign identifier
    - email_template_id (optional): Email template ID
    - sms_template_id (optional): SMS template ID
    - voucher_image_path (required): Path to voucher image file
    - image_base_url (optional): Base URL for voucher images
    - active (optional): Whether campaign is active (default: 1)
    """
    # Require authentication
    auth_token = request.headers.get('Authorization')
    if not auth_token or auth_token != WEBHOOK_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized."}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400
    
    campaign = data.get("campaign", "").strip()
    voucher_image_path = data.get("voucher_image_path", "").strip()
    
    if not campaign or not voucher_image_path:
        return jsonify({
            "status": "error",
            "message": "campaign and voucher_image_path are required"
        }), 400
    
    email_template_id = data.get("email_template_id", "").strip() or None
    sms_template_id = data.get("sms_template_id", "").strip() or None
    image_base_url = data.get("image_base_url", "").strip() or None
    active = data.get("active", 1)
    
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    
    try:
        # Check if campaign exists
        check_query = f"SELECT id FROM {CAMPAIGNS_CONFIG_TABLE} WHERE campaign = %s"
        cursor.execute(check_query, (campaign,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing campaign
            update_query = f"""
            UPDATE {CAMPAIGNS_CONFIG_TABLE} 
            SET email_template_id = %s, sms_template_id = %s, voucher_image_path = %s, 
                image_base_url = %s, active = %s
            WHERE campaign = %s
            """
            cursor.execute(update_query, (
                email_template_id, sms_template_id, voucher_image_path, 
                image_base_url, active, campaign
            ))
            action = "updated"
        else:
            # Create new campaign
            insert_query = f"""
            INSERT INTO {CAMPAIGNS_CONFIG_TABLE} 
                (campaign, email_template_id, sms_template_id, voucher_image_path, image_base_url, active)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                campaign, email_template_id, sms_template_id, voucher_image_path, 
                image_base_url, active
            ))
            action = "created"
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            "status": "success",
            "message": f"Campaign '{campaign}' {action} successfully",
            "campaign": campaign
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating/updating campaign config: {e}")
        if db_conn:
            db_conn.rollback()
            cursor.close()
            db_conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/campaigns-config/<campaign>', methods=['DELETE'])
def delete_campaign_config(campaign):
    """
    Delete a campaign configuration (soft delete by setting active=0).
    Requires Authorization header.
    Or use query parameter hard=true for hard delete.
    """
    # Require authentication
    auth_token = request.headers.get('Authorization')
    if not auth_token or auth_token != WEBHOOK_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized."}), 401
    
    hard_delete = request.args.get('hard', 'false').lower() == 'true'
    
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    
    try:
        if hard_delete:
            delete_query = f"DELETE FROM {CAMPAIGNS_CONFIG_TABLE} WHERE campaign = %s"
            cursor.execute(delete_query, (campaign,))
            action = "deleted"
        else:
            update_query = f"UPDATE {CAMPAIGNS_CONFIG_TABLE} SET active = 0 WHERE campaign = %s"
            cursor.execute(update_query, (campaign,))
            action = "deactivated"
        
        if cursor.rowcount == 0:
            cursor.close()
            db_conn.close()
            return jsonify({"status": "error", "message": f"Campaign '{campaign}' not found"}), 404
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            "status": "success",
            "message": f"Campaign '{campaign}' {action} successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting campaign config: {e}")
        if db_conn:
            db_conn.rollback()
            cursor.close()
            db_conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

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
