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
            # Get credentials from environment variables (file path or JSON string)
            creds_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
            creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
            spreadsheet_input = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
            worksheet_name = os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", "Sheet1")
            
            # Load credentials from file or JSON string
            import json
            creds_dict = None
            
            if creds_file:
                # Try to load from file path
                file_path = creds_file
                if not os.path.isabs(creds_file):
                    # Try relative to current working directory first
                    if not os.path.exists(creds_file):
                        # Try relative to script directory
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        file_path = os.path.join(script_dir, creds_file)
                
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            creds_dict = json.load(f)
                        logger.info(f"Loaded Google Sheets credentials from file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to load credentials from file {file_path}: {e}")
                else:
                    logger.error(f"Credentials file not found: {creds_file} (tried: {file_path})")
            elif creds_json:
                # Try to load from JSON string
                try:
                    creds_dict = json.loads(creds_json)
                    logger.info("Loaded Google Sheets credentials from environment variable")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse credentials JSON string: {e}")
            
            if not creds_dict:
                logger.error("Missing Google Sheets credentials. Set either GOOGLE_SHEETS_CREDENTIALS_FILE or GOOGLE_SHEETS_CREDENTIALS_JSON")
                self.client = None
                self.worksheet = None
                return
            
            if not spreadsheet_input:
                logger.error("Missing GOOGLE_SHEETS_SPREADSHEET_ID in environment variables")
                self.client = None
                self.worksheet = None
                return
            
            # Extract spreadsheet ID from URL or use as-is if it's already an ID
            spreadsheet_id = extract_spreadsheet_id(spreadsheet_input)
            
            if not spreadsheet_id:
                logger.error(f"Could not extract spreadsheet ID from provided input: {spreadsheet_input}")
                self.client = None
                self.worksheet = None
                return
            
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            
            # Authenticate using service account credentials
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            self.client = gspread.authorize(creds)
            logger.info("Successfully authenticated with Google Sheets API")
            
            # Open the spreadsheet
            try:
                self.spreadsheet = self.client.open_by_key(spreadsheet_id)
                logger.info(f"Successfully opened spreadsheet: {self.spreadsheet.title}")
            except Exception as e:
                logger.error(f"Failed to open spreadsheet with ID {spreadsheet_id}. Make sure the service account email ({creds_dict.get('client_email', 'unknown')}) has access to the spreadsheet. Error: {e}")
                raise
            
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

