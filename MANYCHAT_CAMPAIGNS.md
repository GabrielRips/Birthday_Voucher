# ManyChat Campaign Support

The ManyChat webhook endpoint has been optimized to support multiple campaigns with different vouchers. This allows you to run different marketing campaigns simultaneously, each with their own voucher codes and templates.

## Database Schema

The `manychat_vouchers` table now includes:
- `campaign` (required): Campaign identifier
- `email_template_id`: Campaign-specific email template
- `sms_template_id`: Campaign-specific SMS template
- Unique constraint on `(campaign, email)` - same email can be used in different campaigns

## API Endpoints

### POST `/manychat-webhook`

Creates a new voucher for a campaign.

**Request Body:**
```json
{
  "campaign": "summer2024",
  "name": "John Doe",
  "phone": "61412345678",
  "email": "john@example.com",
  "city": "Sydney",
  "email_template_id": "optional_template_id",
  "sms_template_id": "optional_template_id"
}
```

**Required Fields:**
- `campaign`: Campaign identifier (e.g., "summer2024", "birthday2024")
- `name`: Recipient's name
- `phone`: Phone number
- `email`: Email address

**Optional Fields:**
- `city`: City name
- `email_template_id`: Override default email template
- `sms_template_id`: Override default SMS template

**Response:**
```json
{
  "status": "success",
  "campaign": "summer2024",
  "voucher_code": "A7B9C2",
  "issue_date": "2024-01-15",
  "email": true,
  "sms": true
}
```

### GET `/manychat-vouchers`

Query vouchers by campaign.

**Query Parameters:**
- `campaign` (required): Campaign name
- `email` (optional): Filter by specific email
- `limit` (optional): Limit results (default: 100)

**Example:**
```
GET /manychat-vouchers?campaign=summer2024&limit=50
```

**Response:**
```json
{
  "status": "success",
  "campaign": "summer2024",
  "count": 25,
  "vouchers": [
    {
      "id": 1,
      "campaign": "summer2024",
      "name": "John Doe",
      "phone": "61412345678",
      "email": "john@example.com",
      "city": "Sydney",
      "voucher_code": "A7B9C2",
      "issue_date": "2024-01-15",
      "email_sent": 1,
      "sms_sent": 1,
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

### GET `/manychat-campaigns`

Get statistics for all campaigns.

**Response:**
```json
{
  "status": "success",
  "count": 3,
  "campaigns": [
    {
      "campaign": "summer2024",
      "total_vouchers": 150,
      "emails_sent": 148,
      "sms_sent": 149,
      "first_voucher": "2024-01-01T00:00:00",
      "last_voucher": "2024-01-15T23:59:59"
    }
  ]
}
```

## Key Features

1. **Multiple Campaigns**: Run different campaigns simultaneously
2. **Email Reuse**: Same email can be used in different campaigns (unique per campaign)
3. **Campaign-Specific Templates**: Override default email/SMS templates per campaign
4. **Query by Campaign**: Easy filtering and reporting by campaign
5. **Unique Voucher Codes**: Voucher codes remain globally unique across all campaigns

## Database Setup

### New Installation

Run `create_manychat_table.sql` to create the table with campaign support.

### Existing Installation

If you already have the `manychat_vouchers` table, run `migrate_manychat_table.sql` to add campaign support.

## Example Use Cases

### Campaign 1: Summer Promotion
```json
{
  "campaign": "summer2024",
  "name": "Jane Smith",
  "phone": "61412345678",
  "email": "jane@example.com",
  "city": "Melbourne"
}
```

### Campaign 2: Birthday Special
```json
{
  "campaign": "birthday2024",
  "name": "Jane Smith",
  "phone": "61412345678",
  "email": "jane@example.com",
  "city": "Melbourne",
  "email_template_id": "birthday_template_id",
  "sms_template_id": "birthday_sms_template_id"
}
```

Note: The same email (jane@example.com) can be used in both campaigns because they're different campaigns.

## Error Handling

- **Duplicate Email in Same Campaign**: Returns 400 error
- **Missing Required Fields**: Returns 400 error with details
- **Database Errors**: Returns 500 error with error message

