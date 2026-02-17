#!/usr/bin/env python3
"""
Database Reset Script

This script drops all tables to clear the database.
Use this if you need to start fresh after a failed import.
"""

import logging
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def reset_database():
    """Drop all tables from the database"""
    db = Database()
    if not db.connect():
        logger.error("Failed to connect to database")
        return False
    
    try:
        cursor = db.connection.cursor()
        
        # Drop tables in order (respecting foreign key constraints)
        # Drop child tables first
        logger.info("Dropping voucher_redemptions table...")
        cursor.execute("DROP TABLE IF EXISTS voucher_redemptions")
        
        logger.info("Dropping vouchers table...")
        cursor.execute("DROP TABLE IF EXISTS vouchers")
        
        logger.info("Dropping customer table...")
        cursor.execute("DROP TABLE IF EXISTS customer")
        
        db.connection.commit()
        cursor.close()
        
        # Recreate tables
        logger.info("Recreating tables...")
        if not db.create_tables():
            logger.error("Failed to recreate tables")
            return False
        
        logger.info("=" * 60)
        logger.info("Database reset completed successfully!")
        logger.info("All tables have been dropped and recreated.")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.exception(f"Error resetting database: {e}")
        db.connection.rollback()
        return False
    finally:
        db.disconnect()


if __name__ == "__main__":
    import sys
    
    # Safety confirmation
    print("=" * 60)
    print("WARNING: This will DELETE ALL DATA from the database!")
    print("All customers, vouchers, and redemptions will be lost.")
    print("=" * 60)
    
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Reset cancelled.")
        sys.exit(0)
    
    logger.info("Starting database reset...")
    success = reset_database()
    
    if success:
        logger.info("Database reset completed successfully!")
        sys.exit(0)
    else:
        logger.error("Database reset failed!")
        sys.exit(1)

