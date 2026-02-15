# Database Setup Guide for Digital Ocean MySQL

This guide will walk you through setting up the database schema on your Digital Ocean MySQL database.

## Prerequisites

- A Digital Ocean MySQL database instance
- Your database connection credentials from Digital Ocean
- Python 3.8+ installed (if using Method 2)
- MySQL client installed (optional, for Method 1)

---

## Step 1: Get Your Digital Ocean MySQL Connection Details

1. Log in to your [Digital Ocean Dashboard](https://cloud.digitalocean.com/)
2. Navigate to **Databases** → Select your MySQL database
3. Find your connection details:
   - **Host** (e.g., `db-mysql-nyc3-12345-do-user-123456-0.db.ondigitalocean.com`)
   - **Port** (usually `25060` for Digital Ocean MySQL)
   - **Database name** (default database name)
   - **Username** (default user)
   - **Password** (if you haven't set one, you'll need to create/reset it)
   - **SSL Mode** (Digital Ocean requires SSL connections)

### Important Notes:
- Digital Ocean MySQL databases **require SSL connections**
- The default port is usually `25060` (not the standard `3306`)
- You may need to whitelist your IP address in the Digital Ocean firewall settings

---

## Step 2: Set Up Environment Variables

Create a `.env` file in your project root directory (if it doesn't exist) with your database credentials:

```env
# MySQL Database Configuration
MYSQL_HOST=db-mysql-nyc3-12345-do-user-123456-0.db.ondigitalocean.com
MYSQL_PORT=25060
MYSQL_DATABASE=defaultdb
MYSQL_USER=doadmin
MYSQL_PASSWORD=your_secure_password_here
```

**Important:** 
- Replace the values above with your actual Digital Ocean credentials
- Never commit the `.env` file to version control (it should be in `.gitignore`)
- For SSL connections, you may need to add SSL configuration (see Step 3)

---

## Step 3: Configure SSL for Digital Ocean (if needed)

Digital Ocean MySQL requires SSL connections. If you encounter SSL errors, you may need to:

1. Download the CA certificate from Digital Ocean:
   - In your database dashboard, look for "Connection Details" or "Connection Pools"
   - Download the CA certificate file (usually `ca-certificate.crt`)

2. Update your `.env` file to include SSL settings:
```env
MYSQL_SSL_CA=/path/to/ca-certificate.crt
MYSQL_SSL_VERIFY_CERT=true
```

Or if you want to skip SSL verification (not recommended for production):
```env
MYSQL_SSL_DISABLED=false
```

---

## Step 4: Choose Your Setup Method

You have two options to set up the database schema:

### Method 1: Using SQL File Directly (Recommended for Quick Setup)

This method uses the `schema.sql` file directly with a MySQL client.

#### Option A: Using MySQL Command Line Client

1. **Install MySQL client** (if not already installed):
   - Windows: Download from [MySQL website](https://dev.mysql.com/downloads/mysql/)
   - Mac: `brew install mysql-client`
   - Linux: `sudo apt-get install mysql-client`

2. **Connect to your Digital Ocean database**:
   ```bash
   mysql -h YOUR_HOST -P 25060 -u YOUR_USER -p YOUR_DATABASE --ssl-mode=REQUIRED
   ```
   Replace:
   - `YOUR_HOST` with your Digital Ocean host
   - `YOUR_USER` with your username
   - `YOUR_DATABASE` with your database name
   - You'll be prompted for your password

3. **Run the schema file**:
   ```bash
   mysql -h YOUR_HOST -P 25060 -u YOUR_USER -p YOUR_DATABASE --ssl-mode=REQUIRED < schema.sql
   ```

#### Option B: Using Digital Ocean Web Console

1. Go to your database dashboard in Digital Ocean
2. Click on **"Query"** or **"SQL Editor"** (if available)
3. Copy the contents of `schema.sql`
4. Paste and execute the SQL commands

#### Option C: Using MySQL Workbench or DBeaver

1. Create a new connection:
   - Host: Your Digital Ocean host
   - Port: `25060`
   - Username: Your username
   - Password: Your password
   - **Enable SSL** in connection settings
   
2. Connect to the database
3. Open and execute the `schema.sql` file

---

### Method 2: Using Python Script (Programmatic Setup)

This method uses the Python `database.py` module to create tables automatically.

1. **Install Python dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

2. **Create a setup script** (or run Python interactively):
   ```python
   from database import Database
   import logging
   
   # Set up logging to see what's happening
   logging.basicConfig(level=logging.INFO)
   
   # Create database instance
   db = Database()
   
   # Connect to database
   if db.connect():
       print("Connected successfully!")
       
       # Create all tables
       if db.create_tables():
           print("✅ Tables created successfully!")
       else:
           print("❌ Error creating tables")
       
       # Close connection
       db.disconnect()
   else:
       print("❌ Failed to connect to database")
   ```

3. **Save this as `setup_database.py`** and run:
   ```bash
   python setup_database.py
   ```

**Note:** If you encounter SSL errors with Method 2, you may need to update `database.py` to include SSL configuration. See "Troubleshooting SSL Issues" below.

---

## Step 5: Verify the Setup

After running either method, verify that the tables were created:

### Using MySQL Client:
```sql
USE your_database_name;
SHOW TABLES;
```

You should see:
- `customer`
- `vouchers`
- `voucher_redemptions`

### Using Python:
```python
from database import Database

db = Database()
if db.connect():
    cursor = db.connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("Tables created:", [table[0] for table in tables])
    db.disconnect()
```

---

## Step 6: Test the Connection

Test that your application can connect to the database:

```python
from database import Database
import logging

logging.basicConfig(level=logging.INFO)

db = Database()
if db.connect():
    print("✅ Connection successful!")
    
    # Test creating a customer
    customer_id = db.get_or_create_customer(
        name="Test Customer",
        email="test@example.com",
        phone="+1234567890",
        birthday=15,
        birth_month=8
    )
    
    if customer_id:
        print(f"✅ Test customer created with ID: {customer_id}")
        
        # Clean up test data
        # (Optional: delete test customer if desired)
    else:
        print("❌ Failed to create test customer")
    
    db.disconnect()
else:
    print("❌ Connection failed!")
```

---

## Troubleshooting

### SSL Connection Issues

If you get SSL-related errors, you may need to update `database.py` to handle SSL. Add SSL configuration to the `__init__` method:

```python
def __init__(self):
    self.connection = None
    self.config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'database': os.getenv('MYSQL_DATABASE', 'birthday_vouchers'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci',
        # Add SSL configuration for Digital Ocean
        'ssl_disabled': False,
        'ssl_verify_cert': True,
        'ssl_verify_identity': True,
    }
    
    # If you have a CA certificate file
    ssl_ca = os.getenv('MYSQL_SSL_CA')
    if ssl_ca:
        self.config['ssl_ca'] = ssl_ca
```

### Connection Timeout Issues

- Check that your IP address is whitelisted in Digital Ocean firewall settings
- Verify the host, port, username, and password are correct
- Ensure your network allows outbound connections on port 25060

### Authentication Errors

- Double-check your username and password
- Make sure you're using the correct database user (not the root user if it's disabled)
- Verify the database name is correct

### Table Creation Errors

- Ensure you have proper permissions on the database
- Check that the database exists
- Verify foreign key constraints are supported (InnoDB engine)

---

## Next Steps

Once your database is set up:

1. ✅ Verify all three tables exist (`customer`, `vouchers`, `voucher_redemptions`)
2. ✅ Test creating a customer and voucher
3. ✅ Run your application and test the full workflow
4. ✅ Set up your scheduler (see `SCHEDULER_GUIDE.md`)

---

## Quick Reference

**Database Tables:**
- `customer` - Stores customer information
- `vouchers` - Stores voucher information (linked to customers)
- `voucher_redemptions` - Tracks voucher redemptions

**Environment Variables Needed:**
```env
MYSQL_HOST=your_digital_ocean_host
MYSQL_PORT=25060
MYSQL_DATABASE=your_database_name
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
```

**Files:**
- `schema.sql` - SQL schema file
- `database.py` - Python database module
- `.env` - Environment variables (create this file)

---

## Support

If you encounter issues:
1. Check the error messages carefully
2. Verify your connection details
3. Ensure SSL is properly configured
4. Check Digital Ocean database logs in the dashboard

