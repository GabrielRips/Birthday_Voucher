import logging
import os
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import Database
from send_email import MailerSendClient
from send_sms import CellCastClient
from create_voucher_pdf import generate_voucher_pdf
import random
import string

logger = logging.getLogger(__name__)

# Sydney timezone
SYDNEY_TZ = pytz.timezone('Australia/Sydney')


class VoucherScheduler:
    def __init__(self, db: Database, mailer_client: MailerSendClient, sms_client: CellCastClient):
        self.db = db
        self.mailer_client = mailer_client
        self.sms_client = sms_client
        self.scheduler = BackgroundScheduler(timezone=SYDNEY_TZ)
        
    def generate_voucher_code(self):
        """Generate a unique voucher code in format xxxxxxx (7 digits)"""
        max_attempts = 100
        for _ in range(max_attempts):
            # Generate 7 random digits
            voucher_code = ''.join(random.choices(string.digits, k=7))
            
            # Check if code already exists in database
            if not self.db.voucher_code_exists(voucher_code):
                return voucher_code
        
        # Fallback: use timestamp-based code if all random attempts fail
        import time
        timestamp = str(int(time.time()))[-7:]  # Last 7 digits of timestamp
        return timestamp

    def send_notifications(self, voucher, email_template_id=None, sms_template_id=None, is_new_year=False):
        """Send email and SMS notifications for a voucher"""
        email_success = False
        sms_success = False
        
        # Send email if email is provided
        if voucher.get('email'):
            try:
                if is_new_year:
                    # Use new year template
                    email_template_id = os.getenv("MAILERSEND_NEW_YEAR_ID")
                elif not email_template_id:
                    email_template_id = os.getenv("MAILERSEND_DEFAULT_TEMPLATE_ID")
                
                pdf_path = generate_voucher_pdf(voucher['name'], voucher['voucher_code'])
                if pdf_path:
                    email_success = self.mailer_client.send_email(
                        voucher['email'],
                        voucher['name'],
                        email_template_id,
                        pdf_path
                    )
                    # Clean up PDF
                    try:
                        os.remove(pdf_path)
                    except Exception as e:
                        logger.warning(f"Could not delete PDF file {pdf_path}: {e}")
                else:
                    logger.error(f"Failed to generate PDF for {voucher['name']}")
            except Exception as e:
                logger.error(f"Error sending email to {voucher.get('email')}: {e}")
        
        # Send SMS if phone is provided
        if voucher.get('phone'):
            try:
                if is_new_year:
                    # Use new year template
                    sms_template_id = os.getenv("CELLCAST_NEW_YEAR_ID")
                elif not sms_template_id:
                    sms_template_id = os.getenv("CELLCAST_TEMPLATE_ID")
                
                image_url = f"http://170.64.230.163/voucher/voucher_{voucher['voucher_code']}.jpg"
                recipient_data = [{
                    "number": voucher['phone'],
                    "fname": voucher['name'],
                    "custom_value_1": image_url
                }]
                
                sms_success = self.sms_client.send_sms_template(
                    template_id=sms_template_id,
                    numbers=recipient_data
                )
            except Exception as e:
                logger.error(f"Error sending SMS to {voucher.get('phone')}: {e}")
        
        return email_success, sms_success

    def annual_new_year_task(self):
        """Run on January 2nd: Delete all stored vouchers, then send to everyone, issue new codes for the new year"""
        logger.info("Starting annual new year task - January 2nd")
        
        try:
            # Ensure database connection is active
            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
            
            # Delete all stored vouchers first
            logger.info("Deleting all stored vouchers...")
            deleted_count = self.db.delete_all_vouchers()
            logger.info(f"Deleted {deleted_count} vouchers from database")
            
            # Get all customers from database
            customers = self.db.get_all_customers()
            logger.info(f"Processing {len(customers)} customers for new year")
            
            current_year = datetime.now().year
            
            for customer in customers:
                try:
                    customer_id = customer['customer_id']
                    
                    # Generate new voucher code
                    new_voucher_code = self.generate_voucher_code()
                    logger.info(f"Generated new code {new_voucher_code} for {customer['name']}")
                    
                    # Create new voucher for the current year
                    # Set expiration to end of year (December 31st)
                    expires_at = datetime(current_year, 12, 31, 23, 59, 59)
                    
                    voucher_id = self.db.create_voucher(
                        customer_id=customer_id,
                        year=current_year,
                        voucher_code=new_voucher_code,
                        expires_at=expires_at
                    )
                    
                    if voucher_id:
                        # Prepare voucher dict for sending notifications
                        voucher_data = {
                            'name': customer['name'],
                            'email': customer.get('email'),
                            'phone': customer.get('phone'),
                            'voucher_code': new_voucher_code,
                            'birthday': customer.get('birthday'),
                            'birth_month': customer.get('birth_month')
                        }
                        
                        # Send notifications with new year template
                        email_success, sms_success = self.send_notifications(
                            voucher_data,
                            is_new_year=True
                        )
                        
                        logger.info(f"Sent new year notifications to {customer['name']} - Email: {email_success}, SMS: {sms_success}")
                    else:
                        logger.error(f"Failed to create voucher for {customer['name']}")
                        
                except Exception as e:
                    logger.error(f"Error processing customer {customer.get('customer_id')}: {e}")
                    continue
            
            logger.info("Annual new year task completed")
            
        except Exception as e:
            logger.exception(f"Error in annual new year task: {e}")

    def daily_birthday_check_task(self):
        """Run daily at 11am Sydney time: Check birthdays and send reminders"""
        logger.info("Starting daily birthday check task")
        
        try:
            # Ensure database connection is active
            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
            
            # Get current date in Sydney timezone
            now = datetime.now(SYDNEY_TZ)
            current_date = now.date()
            
            # Get all customers from database
            customers = self.db.get_all_customers()
            logger.info(f"Checking {len(customers)} customers for upcoming birthdays")
            
            for customer in customers:
                try:
                    customer_id = customer['customer_id']
                    birthday = customer.get('birthday')
                    birth_month = customer.get('birth_month')
                    
                    # Skip if birthday or birth_month is missing
                    if not birthday or not birth_month:
                        continue
                    
                    # Calculate this year's birthday
                    try:
                        this_year_birthday = datetime(current_date.year, birth_month, birthday).date()
                    except ValueError:
                        # Handle invalid dates (e.g., Feb 30)
                        logger.warning(f"Invalid birthday date for {customer['name']}: {birthday}/{birth_month}")
                        continue
                    
                    # Calculate next birthday (might be next year)
                    if this_year_birthday < current_date:
                        next_birthday = datetime(current_date.year + 1, birth_month, birthday).date()
                    else:
                        next_birthday = this_year_birthday
                    
                    # Calculate days until birthday
                    days_until = (next_birthday - current_date).days
                    
                    # Check if birthday is 1 month away (28-31 days)
                    # Check if birthday is 2 weeks away (13-15 days)
                    email_template_id = None
                    sms_template_id = None
                    should_send = False
                    
                    if 28 <= days_until <= 31:
                        # 1 month away
                        email_template_id = os.getenv("MAILERSEND_MONTH_ID")
                        sms_template_id = os.getenv("CELLCAST_MONTH_ID")
                        should_send = True
                        logger.info(f"{customer['name']} birthday is ~1 month away ({days_until} days)")
                    elif 13 <= days_until <= 15:
                        # 2 weeks away
                        email_template_id = os.getenv("MAILERSEND_2WEEK_ID")
                        sms_template_id = os.getenv("CELLCAST_2WEEK_ID")
                        should_send = True
                        logger.info(f"{customer['name']} birthday is ~2 weeks away ({days_until} days)")
                    
                    if should_send:
                        # Get the most recent voucher for this customer (current year or latest)
                        vouchers = self.db.get_vouchers_by_customer(customer_id)
                        if not vouchers:
                            logger.warning(f"No vouchers found for {customer['name']}, skipping notification")
                            continue
                        
                        # Use the most recent voucher (first in list since ordered by year DESC)
                        voucher = vouchers[0]
                        
                        # Prepare voucher data for sending
                        voucher_data = {
                            'name': customer['name'],
                            'email': customer.get('email'),
                            'phone': customer.get('phone'),
                            'voucher_code': voucher['code'],
                            'birthday': customer.get('birthday'),
                            'birth_month': customer.get('birth_month')
                        }
                        
                        # Send notifications with appropriate template
                        email_success, sms_success = self.send_notifications(
                            voucher_data,
                            email_template_id=email_template_id,
                            sms_template_id=sms_template_id
                        )
                        logger.info(f"Sent birthday reminder to {customer['name']} - Email: {email_success}, SMS: {sms_success}")
                        
                except Exception as e:
                    logger.error(f"Error processing voucher {voucher.get('id')}: {e}")
                    continue
            
            logger.info("Daily birthday check task completed")
            
        except Exception as e:
            logger.exception(f"Error in daily birthday check task: {e}")

    def start(self):
        """Start the scheduler"""
        # Schedule annual task for January 2nd at 9am Sydney time
        self.scheduler.add_job(
            self.annual_new_year_task,
            trigger=CronTrigger(month=1, day=2, hour=9, minute=0, timezone=SYDNEY_TZ),
            id='annual_new_year',
            name='Annual New Year Task',
            replace_existing=True
        )
        
        # Schedule daily task at 11am Sydney time
        self.scheduler.add_job(
            self.daily_birthday_check_task,
            trigger=CronTrigger(hour=11, minute=0, timezone=SYDNEY_TZ),
            id='daily_birthday_check',
            name='Daily Birthday Check',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started - Annual task scheduled for Jan 2 at 9am, Daily task at 11am Sydney time")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

