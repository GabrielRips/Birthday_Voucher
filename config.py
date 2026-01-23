import os
from dotenv import load_dotenv

load_dotenv()

# Flask & general config
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")

# MySQL configuration
MYSQL_HOST=os.getenv("MYSQL_HOST")
MYSQL_PORT=os.getenv("MYSQL_PORT")
MYSQL_USER=os.getenv("MYSQL_USER")
MYSQL_PASSWORD=os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE=os.getenv("MYSQL_DATABASE")
MYSQL_SSL_CA=os.getenv("MYSQL_SSL_CA")
MAIN_TABLE = os.getenv("MYSQL_USERS_TABLE")
MANYCHAT_TABLE = os.getenv("MYSQL_MANYCHAT_TABLE", "manychat_vouchers")

# MailerSend configuration
MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY")
MAILERSEND_SENDER = os.getenv("MAILERSEND_SENDER")
MAILERSEND_WELCOME_TEMPLATE_ID = os.getenv("MAILERSEND_WELCOME_TEMPLATE_ID", "")

# CellCast configuration
CELLCAST_API_KEY = os.getenv("CELLCAST_API_KEY")
CELLCAST_SENDER_ID = os.getenv("CELLCAST_SENDER_ID")
CELLCAST_WELCOME_TEMPLATE_ID = os.getenv("CELLCAST_WELCOME_TEMPLATE_ID", "")

GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
GOOGLE_SHEETS_WORKSHEET =os.getenv("GOOGLE_SHEETS_WORKSHEET")
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

# Campaigns config table
CAMPAIGNS_CONFIG_TABLE = os.getenv("MYSQL_CAMPAIGNS_CONFIG_TABLE", "campaigns_config")

# Global image base URL for voucher images (used for SMS links)
VOUCHER_IMAGE_BASE_URL = os.getenv("VOUCHER_IMAGE_BASE_URL", "http://209.38.84.84/images/")