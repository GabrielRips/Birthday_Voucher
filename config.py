import os
from dotenv import load_dotenv

load_dotenv()

# Flask & general config
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")

# MySQL configuration
MYSQL_HOST=os.getenv("MYSQL_HOST"),
PORT=os.getenv("MYSQL_PORT"),
MYSQL_USER=os.getenv("MYSQL_USER"),
MYSQL_PASSWORD=os.getenv("MYSQL_PASSWORD"),
MYSQL_DATABASE=os.getenv("MYSQL_DATABASE"),
MYSQL_SSL_CA=os.getenv("MYSQL_SSL_CA")

# MailerSend configuration
MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY")
MAILERSEND_SENDER = os.getenv("MAILERSEND_SENDER")
MAILERSEND_WELCOME_TEMPLATE_ID = os.getenv("MAILERSEND_WELCOME_TEMPLATE_ID", "")

# CellCast configuration
CELLCAST_API_KEY = os.getenv("CELLCAST_API_KEY")
CELLCAST_SENDER_ID = os.getenv("CELLCAST_SENDER_ID")
CELLCAST_WELCOME_TEMPLATE_ID = os.getenv("CELLCAST_WELCOME_TEMPLATE_ID", "")
