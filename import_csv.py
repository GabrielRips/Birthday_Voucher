#!/usr/bin/env python3
"""
CSV Import Script for Birthday Voucher System

This script imports data from a CSV file into the database and Google Sheets.
Expected CSV format:
Name, Birthday_DAY, Birthday_MONTH, eMail, Phone, Voucher Code, Email Sent Date, SMS Sent Date, etc.
"""

import csv
import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from database import Database
from google_sheets import GoogleSheetsClient
import pytz

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sydney timezone
SYDNEY_TZ = pytz.timezone('Australia/Sydney')


def parse_date_time(date_str):
    """
    Parse date string from CSV (format: DD/MM/YY HH:MM or similar)
    Returns tuple (date_str, time_str) in format YYYY-MM-DD and HH:MM:SS
    """
    if not date_str or date_str.strip() == '':
        return None, None
    
    date_str = date_str.strip()
    
    # Try different date formats
    date_formats = [
        "%d/%m/%y %H:%M",      # 31/10/24 04:08
        "%d/%m/%Y %H:%M",      # 31/10/2024 04:08
        "%d/%m/%y",            # 31/10/24
        "%d/%m/%Y",            # 31/10/2024
        "%Y-%m-%d %H:%M:%S",   # 2024-10-31 04:08:00
        "%Y-%m-%d",            # 2024-10-31
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Convert to Sydney timezone if not already timezone-aware
            if dt.tzinfo is None:
                dt = SYDNEY_TZ.localize(dt)
            date_part = dt.strftime("%Y-%m-%d")
            time_part = dt.strftime("%H:%M:%S")
            return date_part, time_part
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None, None


def parse_email_sent_status(email_sent_str):
    """Parse email sent status from CSV (TRUE, FALSE, sent, Success, etc.)"""
    if not email_sent_str:
        return False
    
    email_sent_str = str(email_sent_str).strip().upper()
    return email_sent_str in ['TRUE', 'SUCCESS', 'SENT', 'YES', '1']


def parse_sms_sent_status(sms_sent_str, sms_sent_date):
    """Parse SMS sent status from CSV"""
    # If SMS Sent Date exists, assume SMS was sent
    if sms_sent_date and sms_sent_date.strip():
        return True
    
    if not sms_sent_str:
        return False
    
    sms_sent_str = str(sms_sent_str).strip().upper()
    return sms_sent_str in ['TRUE', 'SUCCESS', 'SENT', 'YES', '1']


def normalize_phone(phone_str):
    """Normalize phone number format"""
    if not phone_str:
        return None
    
    # Remove any non-digit characters except +
    phone = ''.join(c for c in str(phone_str) if c.isdigit() or c == '+')
    
    # If it starts with 0, replace with +61
    if phone.startswith('0') and len(phone) == 10:
        phone = '+61' + phone[1:]
    elif phone.startswith('04') and len(phone) == 10:
        phone = '+61' + phone[1:]
    elif not phone.startswith('+'):
        # Assume it's an Australian number without country code
        if len(phone) == 9:
            phone = '+61' + phone
        elif len(phone) == 10 and phone.startswith('4'):
            phone = '+61' + phone
    
    return phone if phone else None


def import_csv_to_database_and_sheets(csv_file_path):
    """
    Import CSV data into database and Google Sheets
    
    Args:
        csv_file_path: Path to the CSV file
    """
    # Initialize database
    db = Database()
    if not db.connect():
        logger.error("Failed to connect to database")
        return False
    
    # Initialize Google Sheets client
    google_sheets = GoogleSheetsClient()
    if not google_sheets.worksheet:
        logger.warning("Google Sheets not available, will only import to database")
    
    # Read CSV file
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        return False
    
    imported_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
                try:
                    # Extract data from CSV row
                    name = row.get('Name', '').strip()
                    if not name:
                        logger.warning(f"Row {row_num}: Skipping row with no name")
                        skipped_count += 1
                        continue
                    
                    birthday_day = row.get('Birthday_DAY', '').strip()
                    birthday_month = row.get('Birthday_MONTH', '').strip()
                    email = row.get('eMail', '').strip() or row.get('Email', '').strip()
                    phone = row.get('Phone', '').strip()
                    voucher_code = row.get('Voucher Code', '').strip()
                    
                    # Parse dates
                    email_sent_date_str = row.get('Email Sent Date', '').strip()
                    sms_sent_date_str = row.get('SMS Sent Date', '').strip()
                    sign_up_date_str = row.get('Sign Up Date', '').strip()
                    
                    # Determine which date to use (prefer Email Sent Date, then Sign Up Date)
                    date_sent_str = email_sent_date_str or sign_up_date_str or sms_sent_date_str
                    date_received, time_received = parse_date_time(date_sent_str)
                    
                    # If no date found, use current date/time
                    if not date_received:
                        now = datetime.now(SYDNEY_TZ)
                        date_received = now.strftime("%Y-%m-%d")
                        time_received = now.strftime("%H:%M:%S")
                    
                    # Parse email and SMS sent status
                    email_sent_str = row.get('Email Sent', '').strip()
                    email_success = parse_email_sent_status(email_sent_str) or bool(email_sent_date_str)
                    
                    sms_sent_str = row.get('SMS Sent', '').strip()
                    sms_success = parse_sms_sent_status(sms_sent_str, sms_sent_date_str)
                    
                    # Normalize phone number
                    phone = normalize_phone(phone) if phone else None
                    
                    # Parse birthday
                    birthday = None
                    birth_month = None
                    try:
                        if birthday_day:
                            birthday = int(birthday_day)
                        if birthday_month:
                            birth_month = int(birthday_month)
                    except ValueError:
                        logger.warning(f"Row {row_num}: Invalid birthday format for {name}")
                    
                    # Create customer in database
                    customer_id = db.get_or_create_customer(
                        name=name,
                        phone=phone,
                        email=email if email else None,
                        birthday=birthday,
                        birth_month=birth_month
                    )
                    
                    if not customer_id:
                        logger.error(f"Row {row_num}: Failed to create/get customer for {name}")
                        error_count += 1
                        continue
                    
                    # Create voucher if voucher code exists
                    if voucher_code:
                        # Extract year from date or use current year
                        try:
                            if date_received:
                                year = int(date_received.split('-')[0])
                            else:
                                year = datetime.now().year
                        except:
                            year = datetime.now().year
                        
                        # Create voucher
                        voucher_id = db.create_voucher(
                            customer_id=customer_id,
                            year=year,
                            voucher_code=voucher_code,
                            expires_at=None
                        )
                        
                        if not voucher_id:
                            logger.warning(f"Row {row_num}: Failed to create voucher for {name}")
                    
                    # Write to Google Sheets
                    if google_sheets.worksheet:
                        # Write entry with date and time from CSV
                        google_sheets.write_entry(
                            name=name,
                            birthday=birthday,
                            birth_month=birth_month,
                            email=email if email else None,
                            phone=phone,
                            email_success=email_success,
                            sms_success=sms_success,
                            date_received=date_received,
                            time_received=time_received
                        )
                    
                    imported_count += 1
                    
                    if imported_count % 100 == 0:
                        logger.info(f"Imported {imported_count} records...")
                    
                except Exception as e:
                    logger.error(f"Row {row_num}: Error processing row: {e}")
                    error_count += 1
                    continue
        
        logger.info("=" * 60)
        logger.info(f"Import completed!")
        logger.info(f"  Successfully imported: {imported_count}")
        logger.info(f"  Skipped: {skipped_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.exception(f"Error reading CSV file: {e}")
        return False
    finally:
        db.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to customer_info.csv if no argument provided
        csv_file = "customer_info.csv"
        logger.info(f"No file specified, using default: {csv_file}")
    else:
        csv_file = sys.argv[1]
    
    logger.info(f"Starting CSV import from: {csv_file}")
    
    success = import_csv_to_database_and_sheets(csv_file)
    
    if success:
        logger.info("Import completed successfully!")
        sys.exit(0)
    else:
        logger.error("Import failed!")
        sys.exit(1)

