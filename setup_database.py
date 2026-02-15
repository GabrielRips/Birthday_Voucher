#!/usr/bin/env python3
"""
Database Setup Script for Birthday Voucher Application
This script helps you set up the database schema on Digital Ocean MySQL.
"""

import sys
import logging
from database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_database():
    """Set up the database schema by creating all required tables"""
    logger.info("Starting database setup...")
    
    # Create database instance
    db = Database()
    
    # Connect to database
    logger.info("Attempting to connect to database...")
    if not db.connect():
        logger.error("❌ Failed to connect to database!")
        logger.error("Please check your .env file and ensure:")
        logger.error("  - MYSQL_HOST is correct")
        logger.error("  - MYSQL_PORT is correct (usually 25060 for Digital Ocean)")
        logger.error("  - MYSQL_USER and MYSQL_PASSWORD are correct")
        logger.error("  - Your IP address is whitelisted in Digital Ocean")
        logger.error("  - SSL is properly configured")
        return False
    
    logger.info("✅ Successfully connected to database!")
    
    # Create all tables
    logger.info("Creating database tables...")
    if db.create_tables():
        logger.info("✅ All tables created successfully!")
        
        # Verify tables were created
        try:
            cursor = db.connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            cursor.close()
            
            expected_tables = ['customer', 'vouchers', 'voucher_redemptions']
            logger.info(f"Tables found: {', '.join(table_names)}")
            
            missing_tables = [t for t in expected_tables if t not in table_names]
            if missing_tables:
                logger.warning(f"⚠️  Missing tables: {', '.join(missing_tables)}")
                return False
            else:
                logger.info("✅ All expected tables are present!")
                
        except Exception as e:
            logger.error(f"Error verifying tables: {e}")
            return False
        
        # Test basic operations
        logger.info("Testing database operations...")
        try:
            # Test creating a customer
            test_customer_id = db.get_or_create_customer(
                name="Test Customer (Delete Me)",
                email="test@example.com",
                phone="+1234567890",
                birthday=1,
                birth_month=1
            )
            
            if test_customer_id:
                logger.info(f"✅ Test customer created with ID: {test_customer_id}")
                
                # Clean up test customer
                cursor = db.connection.cursor()
                cursor.execute("DELETE FROM customer WHERE customer_id = %s", (test_customer_id,))
                db.connection.commit()
                cursor.close()
                logger.info("✅ Test customer cleaned up")
            else:
                logger.warning("⚠️  Could not create test customer (this might be okay)")
                
        except Exception as e:
            logger.warning(f"⚠️  Test operation failed: {e} (this might be okay)")
        
        # Close connection
        db.disconnect()
        logger.info("✅ Database setup completed successfully!")
        return True
        
    else:
        logger.error("❌ Error creating tables!")
        logger.error("Check the error messages above for details")
        db.disconnect()
        return False


def main():
    """Main entry point"""
    print("=" * 60)
    print("Birthday Voucher Database Setup")
    print("=" * 60)
    print()
    
    success = setup_database()
    
    print()
    if success:
        print("=" * 60)
        print("✅ Database setup completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Verify your .env file has all required variables")
        print("  2. Test your application connection")
        print("  3. Set up your scheduler (see SCHEDULER_GUIDE.md)")
        return 0
    else:
        print("=" * 60)
        print("❌ Database setup failed!")
        print("=" * 60)
        print()
        print("Please check:")
        print("  1. Your .env file configuration")
        print("  2. Digital Ocean database connection details")
        print("  3. SSL configuration (Digital Ocean requires SSL)")
        print("  4. IP whitelist settings in Digital Ocean")
        print()
        print("See DATABASE_SETUP_GUIDE.md for detailed instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

