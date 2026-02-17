import mysql.connector
from mysql.connector import Error
import logging
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.connection = None
        # Use birthday database credentials (BIRTHDAY_DB_*) to match universal_voucher_send project
        self.config = {
            'host': os.getenv('BIRTHDAY_DB_HOST', os.getenv('MYSQL_HOST', 'localhost')),
            'database': os.getenv('BIRTHDAY_DB_DATABASE', os.getenv('MYSQL_DATABASE', 'birthday_vouchers')),
            'user': os.getenv('BIRTHDAY_DB_USER', os.getenv('MYSQL_USER', 'root')),
            'password': os.getenv('BIRTHDAY_DB_PASSWORD', os.getenv('MYSQL_PASSWORD', '')),
            'port': int(os.getenv('BIRTHDAY_DB_PORT', os.getenv('MYSQL_PORT', 3306))),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
        
        # SSL configuration for Digital Ocean MySQL (requires SSL)
        ssl_ca = os.getenv('BIRTHDAY_DB_SSL_CA', os.getenv('MYSQL_SSL_CA'))
        ssl_disabled = os.getenv('MYSQL_SSL_DISABLED', 'false').lower() == 'true'
        
        if not ssl_disabled:
            # Digital Ocean MySQL requires SSL
            self.config['ssl_disabled'] = False
            self.config['ssl_verify_cert'] = os.getenv('MYSQL_SSL_VERIFY_CERT', 'true').lower() == 'true'
            self.config['ssl_verify_identity'] = os.getenv('MYSQL_SSL_VERIFY_IDENTITY', 'true').lower() == 'true'
            
            if ssl_ca and os.path.exists(ssl_ca):
                self.config['ssl_ca'] = ssl_ca

    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                logger.info("Successfully connected to MySQL database")
                return True
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")

    def create_tables(self):
        """Create all tables if they don't exist"""
        try:
            conn = self.get_connection()
            if not conn:
                logger.error("Database connection not available for create_tables")
                return False
            cursor = conn.cursor()
            
            # Create customer table
            customer_table = """
            CREATE TABLE IF NOT EXISTS customer (
                customer_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(50),
                email VARCHAR(255),
                birthday INT,
                birth_month INT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_phone (phone),
                INDEX idx_birthday (birth_month, birthday)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            cursor.execute(customer_table)
            
            # Create vouchers table
            vouchers_table = """
            CREATE TABLE IF NOT EXISTS vouchers (
                voucher_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT NOT NULL,
                year INT NOT NULL,
                code VARCHAR(20) UNIQUE NOT NULL,
                status ENUM('active', 'redeemed', 'expired') NOT NULL DEFAULT 'active',
                issued_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE,
                INDEX idx_customer_id (customer_id),
                INDEX idx_code (code),
                INDEX idx_year (year),
                INDEX idx_status (status),
                INDEX idx_expires_at (expires_at),
                UNIQUE KEY unique_customer_year (customer_id, year)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            cursor.execute(vouchers_table)
            
            # Create voucher_redemptions table
            # Note: Using 'location' instead of 'redeemed_location' to match universal_voucher_send project
            redemptions_table = """
            CREATE TABLE IF NOT EXISTS voucher_redemptions (
                redemption_id INT AUTO_INCREMENT PRIMARY KEY,
                voucher_id INT NOT NULL,
                location VARCHAR(100) NULL COMMENT 'Location where voucher was redeemed',
                redeemed_at DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (voucher_id) REFERENCES vouchers(voucher_id) ON DELETE CASCADE,
                INDEX idx_voucher_id (voucher_id),
                INDEX idx_redeemed_at (redeemed_at),
                INDEX idx_location (location)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            cursor.execute(redemptions_table)
            
            conn.commit()
            cursor.close()
            logger.info("All tables created or already exist")
            return True
        except Error as e:
            logger.error(f"Error creating tables: {e}")
            if conn:
                conn.rollback()
            return False

    def get_connection(self):
        """Get the database connection, reconnecting if needed"""
        try:
            if not self.connection or not self.connection.is_connected():
                logger.info("Database connection lost, reconnecting...")
                self.connect()
            return self.connection
        except Exception as e:
            logger.error(f"Error getting database connection: {e}")
            # Try to reconnect
            if self.connect():
                return self.connection
            return None

    # Customer operations
    def get_or_create_customer(self, name, phone=None, email=None, birthday=None, birth_month=None):
        """Get existing customer or create a new one. Returns customer_id"""
        try:
            conn = self.get_connection()
            if not conn:
                logger.error("Database connection not available for get_or_create_customer")
                return None
            cursor = conn.cursor(dictionary=True)
            
            # Try to find existing customer by email or phone
            if email:
                find_query = "SELECT customer_id FROM customer WHERE email = %s"
                cursor.execute(find_query, (email,))
                result = cursor.fetchone()
                if result:
                    cursor.close()
                    logger.info(f"Found existing customer with email {email}: {result['customer_id']}")
                    return result['customer_id']
            
            if phone:
                find_query = "SELECT customer_id FROM customer WHERE phone = %s"
                cursor.execute(find_query, (phone,))
                result = cursor.fetchone()
                if result:
                    cursor.close()
                    logger.info(f"Found existing customer with phone {phone}: {result['customer_id']}")
                    return result['customer_id']
            
            # Create new customer
            insert_query = """
            INSERT INTO customer (name, phone, email, birthday, birth_month)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                name,
                phone if phone else None,
                email if email else None,
                birthday if birthday else None,
                birth_month if birth_month else None
            ))
            conn.commit()
            customer_id = cursor.lastrowid
            cursor.close()
            logger.info(f"Created new customer with ID: {customer_id}")
            return customer_id
        except Error as e:
            logger.error(f"Error getting/creating customer: {e}")
            if conn:
                conn.rollback()
            return None

    def email_exists(self, email):
        """Check if an email already exists in the database"""
        if not email:
            return False
        try:
            conn = self.get_connection()
            if not conn:
                logger.error("Database connection not available for email_exists")
                return False
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM customer WHERE email = %s"
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] > 0
        except Error as e:
            logger.error(f"Error checking email existence: {e}")
            return False

    def get_customer(self, customer_id):
        """Get customer by ID"""
        try:
            conn = self.get_connection()
            if not conn:
                logger.error("Database connection not available for get_customer")
                return None
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM customer WHERE customer_id = %s"
            cursor.execute(query, (customer_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            logger.error(f"Error getting customer: {e}")
            return None

    def get_all_customers(self):
        """Get all customers"""
        try:
            conn = self.get_connection()
            if not conn:
                logger.error("Database connection not available for get_all_customers")
                return []
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM customer"
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            logger.info(f"Retrieved {len(results)} customers from database")
            return results
        except Error as e:
            logger.error(f"Error retrieving customers: {e}")
            return []

    # Voucher operations
    def voucher_code_exists(self, voucher_code):
        """Check if a voucher code already exists in the database"""
        check_query = "SELECT COUNT(*) FROM vouchers WHERE code = %s"
        try:
            conn = self.get_connection()
            if not conn:
                logger.error("Database connection not available for voucher_code_exists")
                return False
            cursor = conn.cursor()
            cursor.execute(check_query, (voucher_code,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] > 0
        except Error as e:
            logger.error(f"Error checking voucher code: {e}")
            return False

    def create_voucher(self, customer_id, year, voucher_code, expires_at=None, status='active', expire_old_vouchers=True):
        """Create a new voucher for a customer. If voucher exists for that year, updates it.
        Optionally expires all previous year vouchers for this customer."""
        try:
            conn = self.get_connection()
            if not conn:
                logger.error("Database connection not available for create_voucher")
                return None
            cursor = conn.cursor()
            
            # Expire old vouchers from previous years (if requested)
            if expire_old_vouchers:
                expire_query = """
                UPDATE vouchers 
                SET status = 'expired' 
                WHERE customer_id = %s AND year < %s AND status != 'redeemed'
                """
                cursor.execute(expire_query, (customer_id, year))
                expired_count = cursor.rowcount
                if expired_count > 0:
                    logger.info(f"Expired {expired_count} old voucher(s) for customer {customer_id}")
            
            # Use INSERT ... ON DUPLICATE KEY UPDATE to handle existing vouchers
            insert_query = """
            INSERT INTO vouchers (customer_id, year, code, status, expires_at)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                code = VALUES(code),
                status = VALUES(status),
                issued_at = CURRENT_TIMESTAMP,
                expires_at = VALUES(expires_at)
            """
            cursor.execute(insert_query, (customer_id, year, voucher_code, status, expires_at))
            conn.commit()
            
            # Get the voucher_id (either newly created or updated)
            select_query = "SELECT voucher_id FROM vouchers WHERE customer_id = %s AND year = %s"
            cursor.execute(select_query, (customer_id, year))
            result = cursor.fetchone()
            voucher_id = result[0] if result else None
            
            cursor.close()
            logger.info(f"Created/updated voucher with ID: {voucher_id} for customer {customer_id}, year {year}, status: {status}")
            return voucher_id
        except Error as e:
            logger.error(f"Error creating voucher: {e}")
            if conn:
                conn.rollback()
            return None

    def get_voucher_by_code(self, voucher_code):
        """Get voucher by code"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT v.*, c.name, c.email, c.phone, c.birthday, c.birth_month
            FROM vouchers v
            JOIN customer c ON v.customer_id = c.customer_id
            WHERE v.code = %s
            """
            cursor.execute(query, (voucher_code,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            logger.error(f"Error getting voucher by code: {e}")
            return None

    def get_vouchers_by_customer(self, customer_id, year=None):
        """Get all vouchers for a customer, optionally filtered by year"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            if year:
                query = """
                SELECT v.*, c.name, c.email, c.phone, c.birthday, c.birth_month
                FROM vouchers v
                JOIN customer c ON v.customer_id = c.customer_id
                WHERE v.customer_id = %s AND v.year = %s
                """
                cursor.execute(query, (customer_id, year))
            else:
                query = """
                SELECT v.*, c.name, c.email, c.phone, c.birthday, c.birth_month
                FROM vouchers v
                JOIN customer c ON v.customer_id = c.customer_id
                WHERE v.customer_id = %s
                ORDER BY v.year DESC
                """
                cursor.execute(query, (customer_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.error(f"Error getting vouchers by customer: {e}")
            return []

    def get_all_vouchers_with_customer_info(self):
        """Get all vouchers with customer information (for scheduler)"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT v.voucher_id, v.customer_id, v.year, v.code, v.status, v.issued_at, v.expires_at,
                   c.name, c.email, c.phone, c.birthday, c.birth_month
            FROM vouchers v
            JOIN customer c ON v.customer_id = c.customer_id
            ORDER BY v.year DESC, v.issued_at DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            logger.info(f"Retrieved {len(results)} vouchers with customer info")
            return results
        except Error as e:
            logger.error(f"Error retrieving vouchers: {e}")
            return []

    def update_voucher_code(self, voucher_id, new_voucher_code):
        """Update the voucher code for a specific voucher"""
        update_query = "UPDATE vouchers SET code = %s WHERE voucher_id = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(update_query, (new_voucher_code, voucher_id))
            self.connection.commit()
            cursor.close()
            logger.info(f"Updated voucher code for voucher_id {voucher_id} to {new_voucher_code}")
            return True
        except Error as e:
            logger.error(f"Error updating voucher code: {e}")
            self.connection.rollback()
            return False

    def delete_voucher(self, voucher_id):
        """Delete a voucher record by ID"""
        delete_query = "DELETE FROM vouchers WHERE voucher_id = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(delete_query, (voucher_id,))
            self.connection.commit()
            cursor.close()
            logger.info(f"Deleted voucher with ID {voucher_id}")
            return True
        except Error as e:
            logger.error(f"Error deleting voucher: {e}")
            self.connection.rollback()
            return False

    def delete_all_vouchers(self):
        """Delete all vouchers from the database"""
        delete_query = "DELETE FROM vouchers"
        try:
            cursor = self.connection.cursor()
            cursor.execute(delete_query)
            deleted_count = cursor.rowcount
            self.connection.commit()
            cursor.close()
            logger.info(f"Deleted all vouchers from database ({deleted_count} vouchers deleted)")
            return deleted_count
        except Error as e:
            logger.error(f"Error deleting all vouchers: {e}")
            self.connection.rollback()
            return 0

    # Voucher status operations
    def update_voucher_status(self, voucher_id, status):
        """Update the status of a voucher (active, redeemed, expired)"""
        if status not in ['active', 'redeemed', 'expired']:
            logger.error(f"Invalid status: {status}. Must be 'active', 'redeemed', or 'expired'")
            return False
        
        update_query = "UPDATE vouchers SET status = %s WHERE voucher_id = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(update_query, (status, voucher_id))
            self.connection.commit()
            cursor.close()
            logger.info(f"Updated voucher {voucher_id} status to {status}")
            return True
        except Error as e:
            logger.error(f"Error updating voucher status: {e}")
            self.connection.rollback()
            return False

    # Redemption operations
    def record_redemption(self, voucher_id, location=None, redeemed_at=None):
        """Record a voucher redemption and update voucher status to 'redeemed'
        Note: Using 'location' parameter to match universal_voucher_send project"""
        if redeemed_at is None:
            redeemed_at = datetime.now()
        
        # Ensure connection is available
        conn = self.get_connection()
        if not conn:
            logger.error("Database connection not available for record_redemption")
            return None
        
        insert_query = """
        INSERT INTO voucher_redemptions (voucher_id, location, redeemed_at)
        VALUES (%s, %s, %s)
        """
        try:
            cursor = conn.cursor()
            cursor.execute(insert_query, (
                voucher_id,
                location if location else None,
                redeemed_at
            ))
            conn.commit()
            redemption_id = cursor.lastrowid
            
            # Update voucher status to 'redeemed'
            self.update_voucher_status(voucher_id, 'redeemed')
            
            cursor.close()
            logger.info(f"Recorded redemption with ID: {redemption_id} for voucher {voucher_id}")
            return redemption_id
        except Error as e:
            logger.error(f"Error recording redemption: {e}")
            conn.rollback()
            return None

    def get_redemptions_by_voucher(self, voucher_id):
        """Get all redemptions for a voucher"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM voucher_redemptions WHERE voucher_id = %s ORDER BY redeemed_at DESC"
            cursor.execute(query, (voucher_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.error(f"Error getting redemptions: {e}")
            return []

    # Legacy method for backward compatibility (creates customer + voucher)
    def insert_voucher(self, name, phone, email, birthday, birth_month, voucher_code):
        """Legacy method: Insert voucher (creates customer if needed, creates voucher for current year)"""
        try:
            # Get or create customer
            customer_id = self.get_or_create_customer(name, phone, email, birthday, birth_month)
            if not customer_id:
                return None
            
            # Get current year
            current_year = datetime.now().year
            
            # Create voucher for current year
            voucher_id = self.create_voucher(customer_id, current_year, voucher_code)
            return voucher_id
        except Exception as e:
            logger.error(f"Error in legacy insert_voucher: {e}")
            return None
