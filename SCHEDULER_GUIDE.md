# Scheduled Tasks Guide

This application includes two automated scheduled tasks that run in the background.

## Task 1: Annual New Year Task (January 2nd)

**Schedule:** Runs every January 2nd at 9:00 AM Sydney time

**What it does:**
1. Retrieves all people from the database
2. Generates a new unique voucher code (BDxxxxxxx format) for each person
3. Updates the database with the new voucher code (replaces the old one)
4. Sends email and SMS notifications to everyone using the "new year" template
5. Includes the new voucher code in the notifications

**Required Environment Variables:**
- `MAILERSEND_NEW_YEAR_ID` - Email template ID for new year messages
- `CELLCAST_NEW_YEAR_ID` - SMS template ID for new year messages

## Task 2: Daily Birthday Reminder Task

**Schedule:** Runs every day at 11:00 AM Sydney time

**What it does:**
1. Checks all people in the database
2. Calculates how many days until each person's next birthday
3. If birthday is **1 month away** (28-31 days):
   - Sends email using `MAILERSEND_MONTH_ID` template
   - Sends SMS using `CELLCAST_MONTH_ID` template
   - Includes their existing voucher code
4. If birthday is **2 weeks away** (13-15 days):
   - Sends email using `MAILERSEND_2WEEK_ID` template
   - Sends SMS using `CELLCAST_2WEEK_ID` template
   - Includes their existing voucher code

**Required Environment Variables:**
- `MAILERSEND_MONTH_ID` - Email template ID for 1-month reminder
- `CELLCAST_MONTH_ID` - SMS template ID for 1-month reminder
- `MAILERSEND_2WEEK_ID` - Email template ID for 2-week reminder
- `CELLCAST_2WEEK_ID` - SMS template ID for 2-week reminder

## Installation

Install required packages:
```bash
pip install -r requirements.txt
```

## Environment Variables

Add these to your `.env` file:

```env
# Existing variables...
MAILERSEND_API_KEY=your_key
MAILERSEND_SENDER=your_sender_email
CELLCAST_API_KEY=your_key
CELLCAST_SENDER_ID=your_sender_id

# New Year Templates
MAILERSEND_NEW_YEAR_ID=your_new_year_email_template_id
CELLCAST_NEW_YEAR_ID=your_new_year_sms_template_id

# Birthday Reminder Templates
MAILERSEND_MONTH_ID=your_month_email_template_id
CELLCAST_MONTH_ID=your_month_sms_template_id
MAILERSEND_2WEEK_ID=your_2week_email_template_id
CELLCAST_2WEEK_ID=your_2week_sms_template_id
```

## How It Works

The scheduler starts automatically when you run `webhook_app.py`. It runs in the background and executes tasks at the scheduled times.

- Tasks run in Sydney timezone (Australia/Sydney)
- All database operations are logged
- Email/SMS sending failures are logged but don't stop the process
- The scheduler continues running even if individual notifications fail

## Testing

To test the scheduler manually, you can call the task functions directly:

```python
from scheduler import VoucherScheduler
from database import Database
from send_email import MailerSendClient
from send_sms import CellCastClient

# Initialize components
db = Database()
db.connect()
mailer = MailerSendClient(...)
sms = CellCastClient(...)

# Create scheduler
scheduler = VoucherScheduler(db, mailer, sms)

# Test annual task
scheduler.annual_new_year_task()

# Test daily task
scheduler.daily_birthday_check_task()
```

