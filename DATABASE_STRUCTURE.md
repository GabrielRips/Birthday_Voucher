# Database Structure Documentation

## Overview

The database uses a normalized 3-table structure that separates customer information, vouchers, and redemption tracking.

## Database Schema

### 1. `customer` Table
Stores customer information.

| Column | Type | Description |
|--------|------|-------------|
| `customer_id` | INT (PK, AUTO_INCREMENT) | Unique customer identifier |
| `name` | VARCHAR(255) | Customer name (required) |
| `phone` | VARCHAR(50) | Phone number (optional) |
| `email` | VARCHAR(255) | Email address (optional) |
| `birthday` | INT | Day of month (1-31, optional) |
| `birth_month` | INT | Month (1-12, optional) |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes:**
- `idx_email` on `email`
- `idx_phone` on `phone`
- `idx_birthday` on `(birth_month, birthday)`

### 2. `vouchers` Table
Stores voucher information linked to customers.

| Column | Type | Description |
|--------|------|-------------|
| `voucher_id` | INT (PK, AUTO_INCREMENT) | Unique voucher identifier |
| `customer_id` | INT (FK) | Reference to `customer.customer_id` |
| `year` | INT | Year the voucher is valid for (e.g., 2026, 2027) |
| `code` | VARCHAR(20) | Unique voucher code (BDxxxxxx format - 6 digits) |
| `status` | ENUM('active', 'redeemed', 'expired') | Voucher status (default: 'active') |
| `issued_at` | DATETIME | When voucher was issued |
| `expires_at` | DATETIME | When voucher expires (optional) |

**Constraints:**
- Foreign key to `customer(customer_id)` with CASCADE delete
- Unique constraint on `code`
- Unique constraint on `(customer_id, year)` - one voucher per customer per year

**Indexes:**
- `idx_customer_id` on `customer_id`
- `idx_code` on `code`
- `idx_year` on `year`
- `idx_status` on `status`
- `idx_expires_at` on `expires_at`

### 3. `voucher_redemptions` Table
Tracks when and where vouchers are redeemed.

| Column | Type | Description |
|--------|------|-------------|
| `redemption_id` | INT (PK, AUTO_INCREMENT) | Unique redemption identifier |
| `voucher_id` | INT (FK) | Reference to `vouchers.voucher_id` |
| `redeemed_location` | VARCHAR(255) | Where voucher was redeemed (optional) |
| `redeemed_at` | DATETIME | Date and time of redemption |

**Constraints:**
- Foreign key to `vouchers(voucher_id)` with CASCADE delete

**Indexes:**
- `idx_voucher_id` on `voucher_id`
- `idx_redeemed_at` on `redeemed_at`

## Design Benefits

### ✅ **Normalization**
- Customer data is stored once and referenced by vouchers
- Reduces data duplication
- Easier to update customer information

### ✅ **Multiple Vouchers Per Customer**
- Supports one voucher per customer per year
- Historical voucher data is preserved
- Easy to query vouchers by year

### ✅ **Redemption Tracking**
- Complete audit trail of voucher redemptions
- Can track multiple redemptions per voucher (if needed)
- Location and timestamp tracking

### ✅ **Data Integrity**
- Foreign key constraints ensure referential integrity
- Unique constraints prevent duplicate vouchers
- CASCADE deletes maintain consistency

## Usage Examples

### Create a Customer and Voucher
```python
# Get or create customer
customer_id = db.get_or_create_customer(
    name="John Doe",
    email="john@example.com",
    phone="+61412345678",
    birthday=15,
    birth_month=8
)

# Create voucher for current year
voucher_id = db.create_voucher(
    customer_id=customer_id,
    year=2026,
    voucher_code="BD123456",
    expires_at=datetime(2026, 12, 31, 23, 59, 59),
    status='active'  # Default is 'active'
)
```

### Record a Redemption
```python
# This automatically updates voucher status to 'redeemed'
db.record_redemption(
    voucher_id=voucher_id,
    redeemed_location="Sydney Store",
    redeemed_at=datetime.now()  # Single datetime field
)
```

### Update Voucher Status
```python
# Manually update voucher status
db.update_voucher_status(voucher_id, 'expired')
```

### Get Customer's Vouchers
```python
# Get all vouchers for a customer
vouchers = db.get_vouchers_by_customer(customer_id)

# Get voucher for specific year
vouchers_2026 = db.get_vouchers_by_customer(customer_id, year=2026)
```

## Migration Notes

If migrating from the old single-table structure:
1. Extract unique customers from old vouchers table
2. Create customer records
3. Create voucher records linked to customers
4. Preserve original `created_at` timestamps where possible

## Status Field Values

The `status` field in the `vouchers` table can have three values:
- **`active`** - Voucher is active and can be used (default)
- **`redeemed`** - Voucher has been redeemed (automatically set when recording redemption)
- **`expired`** - Voucher has expired (can be set manually or via scheduled task)

## Future Enhancements

1. **Add `notes` field** to customer table for additional information
2. **Add `redemption_count`** tracking if multiple redemptions are allowed
3. **Automatic expiration checking** - Scheduled task to mark expired vouchers

