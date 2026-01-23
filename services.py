import datetime
import logging
import secrets
import string
from db import get_db_connection
from config import MAIN_TABLE, MANYCHAT_TABLE, CAMPAIGNS_CONFIG_TABLE

def generate_random_voucher_code():
    """
    Generates a random, cryptographically secure voucher code.
    Format: 6 alphanumeric characters (uppercase letters and digits).
    Example: A7B9C2, X3K9M8
    """
    # Generate 6 random alphanumeric characters (uppercase + digits)
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(6))

def get_next_voucher_code():
    """
    Generates a unique random voucher code by checking against existing codes.
    Uses cryptographically secure random generation to prevent guessing.
    """
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    
    max_attempts = 100  # Prevent infinite loop
    for _ in range(max_attempts):
        new_code = generate_random_voucher_code()
        
        # Check if code already exists in MAIN_TABLE
        query = f"SELECT id FROM {MAIN_TABLE} WHERE voucher_code = %s"
        cursor.execute(query, (new_code,))
        if cursor.fetchone():
            continue  # Code exists, try again
        
        # Check if code exists in MANYCHAT_TABLE
        query = f"SELECT id FROM {MANYCHAT_TABLE} WHERE voucher_code = %s"
        cursor.execute(query, (new_code,))
        if cursor.fetchone():
            continue  # Code exists, try again
        
        # Unique code found
        cursor.close()
        db_conn.close()
        return new_code
    
    # If we somehow exhausted all attempts (extremely unlikely)
    cursor.close()
    db_conn.close()
    raise Exception("Failed to generate unique voucher code after maximum attempts")

def get_next_manychat_voucher_code():
    """
    Generates a unique random voucher code for ManyChat campaigns.
    Checks both MAIN_TABLE and MANYCHAT_TABLE to ensure uniqueness across both.
    Uses cryptographically secure random generation to prevent guessing.
    """
    # Reuse the same random generation function
    return get_next_voucher_code()

def get_campaign_config(campaign):
    """
    Retrieves campaign configuration from the campaigns_config table.
    Returns a dictionary with email_template_id, sms_template_id, voucher_image_path, and image_base_url.
    Returns None if campaign not found.
    """
    db_conn = get_db_connection()
    cursor = db_conn.cursor(dictionary=True)
    
    try:
        query = f"SELECT * FROM {CAMPAIGNS_CONFIG_TABLE} WHERE campaign = %s AND active = 1"
        cursor.execute(query, (campaign,))
        result = cursor.fetchone()
        
        if result:
            config = {
                'email_template_id': result.get('email_template_id'),
                'sms_template_id': result.get('sms_template_id'),
                'voucher_image_path': result.get('voucher_image_path'),
                'image_base_url': result.get('image_base_url')
            }
        else:
            config = None
        
        cursor.close()
        db_conn.close()
        return config
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching campaign config: {e}")
        cursor.close()
        db_conn.close()
        return None

# You can add additional business logic functions here if needed.
