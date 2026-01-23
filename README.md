# Birthday_Voucher

A Flask application for managing birthday vouchers, sending email/SMS notifications, and integrating with Google Sheets.

## Prerequisites

- Python 3.7 or higher
- MySQL database
- Environment variables configured (see below)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Flask & general config
WEBHOOK_SECRET_TOKEN=your_secret_token_here

# MySQL configuration
MYSQL_HOST=your_mysql_host
MYSQL_PORT=3306
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_database_name
MYSQL_SSL_CA=path_to_ssl_ca_file
MYSQL_USERS_TABLE=your_users_table_name

# MailerSend configuration
MAILERSEND_API_KEY=your_mailersend_api_key
MAILERSEND_SENDER=your_sender_email
MAILERSEND_WELCOME_TEMPLATE_ID=your_welcome_template_id
MAILERSEND_1ST_2WEEKS_ID=your_first_2weeks_template_id
MAILERSEND_2ND_2WEEKS_ID=your_second_2weeks_template_id
MAILERSEND_1MONTH_ID=your_1month_template_id

# CellCast configuration
CELLCAST_API_KEY=your_cellcast_api_key
CELLCAST_SENDER_ID=your_sender_id
CELLCAST_WELCOME_TEMPLATE_ID=your_welcome_template_id
CELLCAST_1ST_2WEEKS_ID=your_first_2weeks_template_id
CELLCAST_2ND_2WEEKS_ID=your_second_2weeks_template_id
CELLCAST_1MONTH_ID=your_1month_template_id

# Google Sheets configuration
GOOGLE_SHEETS_ID=your_google_sheets_id
GOOGLE_SHEETS_WORKSHEET=your_worksheet_name
GOOGLE_SHEETS_CREDENTIALS=your_google_sheets_credentials_json
```

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://0.0.0.0:8000` (accessible on all network interfaces on port 8000).

## API Endpoints

### POST `/signup`
Register a new user with birthday voucher.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone_number": "+1234567890",
  "birth_day": 15,
  "birth_month": 6
}
```

### GET `/daily-check`
Daily endpoint to update voucher codes and send birthday reminders. Requires Authorization header.

**Headers:**
```
Authorization: your_webhook_secret_token
```

## Voucher Lookup Application

The `voucher_lookup` directory contains a PHP web application for looking up and confirming voucher usage.

### Prerequisites for Voucher Lookup

- PHP 7.4 or higher
- Composer (PHP dependency manager)
- MySQL database access

### Setup Instructions for Voucher Lookup

1. **Install PHP Dependencies**

   Navigate to the `voucher_lookup` directory and install Composer dependencies:

   ```bash
   cd voucher_lookup
   composer install
   ```

2. **Configure Environment Variables**

   Create a `.env` file in the `voucher_lookup` directory with the following variables:

   ```env
   # MySQL configuration (same as main app)
   MYSQL_HOST=your_mysql_host
   MYSQL_PORT=3306
   MYSQL_USER=your_mysql_user
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=your_database_name
   MYSQL_SSL_CA=path_to_ssl_ca_file
   MYSQL_USERS_TABLE=your_users_table_name
   MYSQL_VOUCHER_LOG_TABLE=your_voucher_log_table_name

   # Site password for login
   SITE_PASSWORD=your_site_password
   ```

3. **Run the PHP Development Server**

   From the `voucher_lookup` directory, start PHP's built-in server:

   ```bash
   php -S localhost:8080
   ```

   Or if you prefer a different port:

   ```bash
   php -S localhost:8080 -t .
   ```

   The application will be accessible at `http://localhost:8080`

### Using the Voucher Lookup

1. Navigate to `http://localhost:8080` in your browser
2. You'll be redirected to `login.php` - enter the password from your `.env` file
3. After logging in, you can enter voucher codes to look up customer details
4. Click "Confirm Voucher Use" to mark a voucher as claimed

## Notes

- Ensure the MySQL database and tables are set up before running
- The application generates PDF vouchers and sends them via email
- SMS notifications are sent via CellCast
- Signup data is automatically appended to Google Sheets
- For production, use a proper web server (Apache/Nginx) instead of PHP's built-in server