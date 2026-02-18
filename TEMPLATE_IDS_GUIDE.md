# Template IDs Configuration Guide

This guide shows you where to put all the template IDs for **CellCast** (SMS) and **MailerSend** (Email) services.

## Where to Put Template IDs

**All template IDs should be added to your `.env` file** in the project root directory.

---

## Complete Template ID List

Add these environment variables to your `.env` file:

### MailerSend (Email) Template IDs

```env
# Default/General Templates
MAILERSEND_DEFAULT_TEMPLATE_ID=your_default_email_template_id

# Annual New Year Task (January 2nd)
MAILERSEND_NEW_YEAR_ID=your_new_year_email_template_id

# Birthday Reminder Templates (Scheduled Tasks)
MAILERSEND_MONTH_ID=your_1month_reminder_email_template_id
MAILERSEND_2WEEK_ID=your_2week_reminder_email_template_id
```

### CellCast (SMS) Template IDs

```env
# Default/General Templates
CELLCAST_TEMPLATE_ID=your_default_sms_template_id

# Annual New Year Task (January 2nd)
CELLCAST_NEW_YEAR_ID=your_new_year_sms_template_id

# Birthday Reminder Templates (Scheduled Tasks)
CELLCAST_MONTH_ID=your_1month_reminder_sms_template_id
CELLCAST_2WEEK_ID=your_2week_reminder_sms_template_id
```

---

## Where Each Template is Used

### 1. **Annual New Year Task** (Runs January 2nd at 9am Sydney time)

**Location:** `scheduler.py` - `annual_new_year_task()` method

**Templates Used:**
- `MAILERSEND_NEW_YEAR_ID` - Email template for new year messages
- `CELLCAST_NEW_YEAR_ID` - SMS template for new year messages

**What it does:** Sends new year vouchers to all customers in the database.

---

### 2. **Daily Birthday Reminder Task** (Runs daily at 11am Sydney time)

**Location:** `scheduler.py` - `daily_birthday_check_task()` method

**Templates Used:**

**1 Month Reminder (exactly 30 days before birthday):**
- `MAILERSEND_MONTH_ID` - Email template
- `CELLCAST_MONTH_ID` - SMS template

**2 Week Reminder (exactly 14 days before birthday):**
- `MAILERSEND_2WEEK_ID` - Email template
- `CELLCAST_2WEEK_ID` - SMS template

**What it does:** Checks all customers and sends reminders when their birthday is approaching.

---

### 3. **Webhook Endpoint** (`/birthday-webhook`)

**Location:** `webhook_app.py` - `birthday_webhook()` function

**Templates Used:**
- `MAILERSEND_DEFAULT_TEMPLATE_ID` - Email template for all webhook requests
- `CELLCAST_TEMPLATE_ID` - SMS template for all webhook requests

**What it does:** Handles incoming webhook requests to create vouchers and send notifications using the default templates.

---

### 4. **Fallback Templates**

**Location:** Used in `scheduler.py` - `send_notifications()` method

**Templates Used:**
- `MAILERSEND_DEFAULT_TEMPLATE_ID` - Fallback email template
- `CELLCAST_TEMPLATE_ID` - Fallback SMS template

**What it does:** Used when no specific template is provided or when template lookup fails.

---

## Example `.env` File

Here's a complete example of what your `.env` file should look like:

```env
# Database Configuration
MYSQL_HOST=your_database_host
MYSQL_PORT=25060
MYSQL_DATABASE=your_database_name
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password

# MailerSend Configuration
MAILERSEND_API_KEY=your_mailersend_api_key
MAILERSEND_SENDER=your_sender_email@example.com

# MailerSend Template IDs
MAILERSEND_DEFAULT_TEMPLATE_ID=abc123xyz
MAILERSEND_NEW_YEAR_ID=def456uvw
MAILERSEND_MONTH_ID=ghi789rst
MAILERSEND_2WEEK_ID=jkl012mno

# CellCast Configuration
CELLCAST_API_KEY=your_cellcast_api_key
CELLCAST_SENDER_ID=your_sender_id

# CellCast Template IDs
CELLCAST_TEMPLATE_ID=hij234klm
CELLCAST_NEW_YEAR_ID=nop567qrs
CELLCAST_MONTH_ID=tuv890wxy
CELLCAST_2WEEK_ID=zab123cde

# Webhook Security
WEBHOOK_SECRET_TOKEN=your_webhook_secret_token
```

---

## How to Get Your Template IDs

### MailerSend Template IDs

1. Log in to your [MailerSend Dashboard](https://app.mailersend.com/)
2. Navigate to **Templates** → **Email Templates**
3. Click on the template you want to use
4. The template ID is usually visible in the URL or template details
5. Copy the template ID and add it to your `.env` file

### CellCast Template IDs

1. Log in to your CellCast account
2. Navigate to **Templates** or use the API to get templates
3. Use the CellCast API endpoint to retrieve template IDs:
   ```
   GET https://cellcast.com.au/api/v3/get-template
   ```
4. Copy the template ID from the response
5. Add it to your `.env` file

---

## Template ID Mapping Reference

### For Scheduled Tasks (Automatic)

| Task | When | Email Template | SMS Template |
|------|------|----------------|--------------|
| New Year | Jan 2, 9am | `MAILERSEND_NEW_YEAR_ID` | `CELLCAST_NEW_YEAR_ID` |
| 1 Month Reminder | Daily check, exactly 30 days before | `MAILERSEND_MONTH_ID` | `CELLCAST_MONTH_ID` |
| 2 Week Reminder | Daily check, exactly 14 days before | `MAILERSEND_2WEEK_ID` | `CELLCAST_2WEEK_ID` |

### For Webhook Calls (Manual/API)

| Email Template | SMS Template |
|----------------|--------------|
| `MAILERSEND_DEFAULT_TEMPLATE_ID` | `CELLCAST_TEMPLATE_ID` |

**Note:** All webhook requests use the default templates regardless of any `templateType` parameter.

---

## Important Notes

1. **All template IDs are optional** - If a template ID is missing, the system will:
   - For scheduled tasks: Skip sending that notification type (email or SMS)
   - For webhooks: Fall back to the default template

2. **Template IDs are strings** - They can be alphanumeric and may include hyphens or other characters

3. **Keep your `.env` file secure** - Never commit it to version control (it's already in `.gitignore`)

4. **Test your templates** - Make sure your templates in MailerSend and CellCast are properly configured with the correct merge fields/variables

---

## Troubleshooting

### Template ID Not Working

1. **Verify the template ID is correct:**
   - Check the ID in your MailerSend/CellCast dashboard
   - Ensure there are no extra spaces in your `.env` file

2. **Check template variables:**
   - MailerSend templates should have `{{ username }}` variable
   - CellCast templates should have merge fields like `fname`, `custom_value_1`, etc.

3. **Check logs:**
   - Look at `app.log` for error messages
   - Check that template IDs are being loaded correctly

### Missing Template ID Error

If you see errors about missing template IDs:
- Ensure all required template IDs are in your `.env` file
- Restart your application after adding new template IDs
- Check that the `.env` file is in the project root directory

---

## Quick Checklist

- [ ] All MailerSend template IDs added to `.env`
- [ ] All CellCast template IDs added to `.env`
- [ ] Template IDs match the IDs in your MailerSend/CellCast dashboards
- [ ] No extra spaces or quotes around template IDs
- [ ] Application restarted after adding template IDs
- [ ] Templates tested with sample data

