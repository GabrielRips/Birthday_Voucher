import gspread
from google.oauth2.service_account import Credentials
import os
import logging
from datetime import datetime
import pytz
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
                        "Date Received",
                        "Time Received",
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
                    "Date Received",
                    "Time Received",
                    "Email Sent Successfully",
                    "SMS Sent Successfully"
                ])
                logger.info(f"Created new worksheet: {worksheet_name}")
            
            logger.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            logger.exception(f"Failed to initialize Google Sheets client: {e}")
            self.client = None
            self.worksheet = None
    
    def write_entry(self, name, birthday, birth_month, email, phone, email_success, sms_success, date_received=None, time_received=None):
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
            date_received: Optional date string in format YYYY-MM-DD (defaults to current date)
            time_received: Optional time string in format HH:MM:SS (defaults to current time)
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
            
            # Format date and time received (separate columns) - using Sydney timezone
            if date_received and time_received:
                # Use provided date and time
                date_received_str = date_received
                time_received_str = time_received
            else:
                # Use current date and time in Sydney timezone
                sydney_tz = pytz.timezone('Australia/Sydney')
                now_sydney = datetime.now(sydney_tz)
                date_received_str = now_sydney.strftime("%Y-%m-%d")
                time_received_str = now_sydney.strftime("%H:%M:%S")
            
            # Format success statuses
            email_status = "Yes" if email_success else "No"
            sms_status = "Yes" if sms_success else "No"
            
            # Find the next empty row in column A
            all_values = self.worksheet.col_values(1)  # Get all values in column A
            next_row = len(all_values) + 1
            
            # Prepare row data
            row = [
                name or "",
                birthday_str,
                email or "",
                phone or "",
                date_received_str,
                time_received_str,
                email_status,
                sms_status
            ]
            
            # Write to specific range starting from column A
            range_name = f"A{next_row}:H{next_row}"
            self.worksheet.update(range_name, [row], value_input_option='USER_ENTERED')
            logger.info(f"Successfully wrote entry to Google Sheets for {name} at row {next_row}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to write entry to Google Sheets: {e}")
            return False
    
    def write_entries_batch(self, entries):
        """
        Write multiple entries to Google Sheets in a single batch operation.
        This is more efficient and helps avoid rate limits.
        
        Args:
            entries: List of dictionaries with keys: name, birthday, birth_month, email, phone, 
                    email_success, sms_success, date_received (optional), time_received (optional)
        
        Returns:
            Number of entries successfully written
        """
        if not self.worksheet:
            logger.warning("Google Sheets worksheet not available. Skipping batch write operation.")
            return 0
        
        if not entries:
            return 0
        
        rows = []
        for entry in entries:
            try:
                # Format birthday (combine day and month)
                birthday_str = ""
                birthday = entry.get('birthday')
                birth_month = entry.get('birth_month')
                if birthday and birth_month:
                    birthday_str = f"{birthday}/{birth_month}"
                elif birthday:
                    birthday_str = str(birthday)
                elif birth_month:
                    birthday_str = f"Month: {birth_month}"
                
                # Format date and time received
                date_received = entry.get('date_received')
                time_received = entry.get('time_received')
                if date_received and time_received:
                    date_received_str = date_received
                    time_received_str = time_received
                else:
                    # Use current date and time in Sydney timezone
                    sydney_tz = pytz.timezone('Australia/Sydney')
                    now_sydney = datetime.now(sydney_tz)
                    date_received_str = now_sydney.strftime("%Y-%m-%d")
                    time_received_str = now_sydney.strftime("%H:%M:%S")
                
                # Format success statuses
                email_status = "Yes" if entry.get('email_success') else "No"
                sms_status = "Yes" if entry.get('sms_success') else "No"
                
                # Create row
                row = [
                    entry.get('name') or "",
                    birthday_str,
                    entry.get('email') or "",
                    entry.get('phone') or "",
                    date_received_str,
                    time_received_str,
                    email_status,
                    sms_status
                ]
                rows.append(row)
            except Exception as e:
                logger.error(f"Error formatting entry for batch write: {e}")
                continue
        
        if not rows:
            return 0
        
        # Write in batches with retry logic
        import time
        max_retries = 3
        batch_size = 100  # Google Sheets allows up to 500, but we use 100 to be safe
        
        written_count = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            retries = 0
            success = False
            
            while retries < max_retries and not success:
                try:
                    self.worksheet.append_rows(batch)
                    written_count += len(batch)
                    success = True
                    logger.info(f"Wrote batch of {len(batch)} rows to Google Sheets ({written_count}/{len(rows)} total)")
                except Exception as e:
                    retries += 1
                    if "429" in str(e) or "Quota exceeded" in str(e):
                        # Rate limit error - wait with exponential backoff
                        wait_time = (2 ** retries) * 60  # 2, 4, 8 minutes
                        logger.warning(f"Rate limit hit. Waiting {wait_time} seconds before retry {retries}/{max_retries}...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Error writing batch to Google Sheets: {e}")
                        if retries >= max_retries:
                            raise
                        time.sleep(5)  # Short wait for other errors
            
            # Small delay between batches to avoid hitting rate limits
            if i + batch_size < len(rows):
                time.sleep(2)  # 2 second delay between batches
        
        return written_count

