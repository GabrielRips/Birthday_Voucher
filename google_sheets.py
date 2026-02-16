import gspread
from google.oauth2.service_account import Credentials
import os
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

def extract_spreadsheet_id(spreadsheet_input):
    """
    Extract spreadsheet ID from a Google Sheets URL or return the input if it's already an ID.
    
    Args:
        spreadsheet_input: Either a full Google Sheets URL or just the spreadsheet ID
        
    Returns:
        The spreadsheet ID
    """
    if not spreadsheet_input:
        return None
    
    # Check if it's a URL
    url_pattern = r'https?://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)'
    match = re.search(url_pattern, spreadsheet_input)
    
    if match:
        # Extract ID from URL
        return match.group(1)
    else:
        # Assume it's already an ID
        return spreadsheet_input.strip()

class GoogleSheetsClient:
    def __init__(self):
        """Initialize Google Sheets client using service account credentials."""
        try:
            # Get credentials from environment variables
            creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
            spreadsheet_input = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
            worksheet_name = os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", "Sheet1")
            
            if not creds_json or not spreadsheet_input:
                logger.error("Missing Google Sheets credentials or spreadsheet ID in environment variables")
                self.client = None
                self.worksheet = None
                return
            
            # Extract spreadsheet ID from URL or use as-is if it's already an ID
            spreadsheet_id = extract_spreadsheet_id(spreadsheet_input)
            
            if not spreadsheet_id:
                logger.error("Could not extract spreadsheet ID from provided input")
                self.client = None
                self.worksheet = None
                return
            
            # Parse credentials JSON string
            import json
            creds_dict = json.loads(creds_json)
            
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            
            # Authenticate using service account credentials
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            self.client = gspread.authorize(creds)
            
            # Open the spreadsheet
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # Get or create the worksheet
            try:
                self.worksheet = self.spreadsheet.worksheet(worksheet_name)
                # Check if headers exist, if not add them
                existing_data = self.worksheet.get_all_values()
                if not existing_data or len(existing_data) == 0:
                    # Worksheet exists but is empty, add headers
                    self.worksheet.append_row([
                        "Person Name",
                        "Birthday",
                        "Email",
                        "Phone Number",
                        "Datetime Received",
                        "Email Sent Successfully",
                        "SMS Sent Successfully"
                    ])
                    logger.info(f"Added headers to empty worksheet: {worksheet_name}")
            except gspread.exceptions.WorksheetNotFound:
                # Create worksheet if it doesn't exist
                self.worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)
                # Add headers
                self.worksheet.append_row([
                    "Person Name",
                    "Birthday",
                    "Email",
                    "Phone Number",
                    "Datetime Received",
                    "Email Sent Successfully",
                    "SMS Sent Successfully"
                ])
                logger.info(f"Created new worksheet: {worksheet_name}")
            
            logger.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            logger.exception(f"Failed to initialize Google Sheets client: {e}")
            self.client = None
            self.worksheet = None
    
    def write_entry(self, name, birthday, birth_month, email, phone, email_success, sms_success):
        """
        Write an entry to Google Sheets.
        
        Args:
            name: Person's name
            birthday: Day of month (1-31)
            birth_month: Month (1-12)
            email: Email address
            phone: Phone number
            email_success: Boolean indicating if email was sent successfully
            sms_success: Boolean indicating if SMS was sent successfully
        """
        if not self.worksheet:
            logger.warning("Google Sheets worksheet not available. Skipping write operation.")
            return False
        
        try:
            # Format birthday (combine day and month)
            birthday_str = ""
            if birthday and birth_month:
                birthday_str = f"{birthday}/{birth_month}"
            elif birthday:
                birthday_str = str(birthday)
            elif birth_month:
                birthday_str = f"Month: {birth_month}"
            
            # Format datetime received
            datetime_received = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format success statuses
            email_status = "Yes" if email_success else "No"
            sms_status = "Yes" if sms_success else "No"
            
            # Append row to worksheet
            row = [
                name or "",
                birthday_str,
                email or "",
                phone or "",
                datetime_received,
                email_status,
                sms_status
            ]
            
            self.worksheet.append_row(row)
            logger.info(f"Successfully wrote entry to Google Sheets for {name}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to write entry to Google Sheets: {e}")
            return False

