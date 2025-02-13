import datetime
from db import get_db_connection
from config import MAIN_TABLE

def get_next_voucher_code():
    """
    Scans the users table for the highest voucher code number and returns the next code.
    Assumes voucher codes are stored in the format "TWC-<number>".
    """
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    query = (f"SELECT MAX(CAST(SUBSTRING(voucher_code, LOCATE('-', voucher_code)+1) AS UNSIGNED)) "
             f"FROM {MAIN_TABLE}")
    cursor.execute(query)
    result = cursor.fetchone()
    max_code = result[0] if result[0] is not None else 999  # Start at 1000 if none exists
    next_code = "TWC-" + str(max_code + 1)
    cursor.close()
    db_conn.close()
    return next_code

# You can add additional business logic functions here if needed.
