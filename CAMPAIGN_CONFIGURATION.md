# Campaign Configuration Guide

Each campaign now stores its own email template, SMS template, and voucher image. This allows you to have completely different voucher designs and messaging for each campaign.

## Database Setup

### Create Campaigns Config Table

Run the SQL script to create the campaigns configuration table:

```sql
-- Run create_campaigns_config_table.sql
```

## Campaign Configuration Fields

- **campaign** (required): Unique campaign identifier
- **email_template_id** (optional): MailerSend email template ID
- **sms_template_id** (optional): CellCast SMS template ID  
- **voucher_image_path** (required): Path to the base voucher image file (JPG/PNG)
- **image_base_url** (optional): Base URL for voucher images (defaults to http://209.38.84.84/images/)
- **active** (optional): Whether campaign is active (default: 1)

## API Endpoints

### Create/Update Campaign Configuration

**POST** `/campaigns-config`

Creates a new campaign configuration or updates an existing one.

**Request Body:**
```json
{
  "campaign": "summer2024",
  "email_template_id": "abc123",
  "sms_template_id": "xyz789",
  "voucher_image_path": "assests/campaigns/summer2024_voucher.jpg",
  "image_base_url": "http://209.38.84.84/images/",
  "active": 1
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Campaign 'summer2024' created successfully",
  "campaign": "summer2024"
}
```

### Get Campaign Configuration(s)

**GET** `/campaigns-config`

Get all campaign configurations.

**GET** `/campaigns-config?campaign=summer2024`

Get specific campaign configuration.

**Response:**
```json
{
  "status": "success",
  "config": {
    "id": 1,
    "campaign": "summer2024",
    "email_template_id": "abc123",
    "sms_template_id": "xyz789",
    "voucher_image_path": "assests/campaigns/summer2024_voucher.jpg",
    "image_base_url": "http://209.38.84.84/images/",
    "active": 1,
    "created_at": "2024-01-15T10:00:00",
    "updated_at": "2024-01-15T10:00:00"
  }
}
```

### Delete/Deactivate Campaign

**DELETE** `/campaigns-config/<campaign>`

Soft delete (deactivates campaign):
```
DELETE /campaigns-config/summer2024
```

Hard delete (permanently removes):
```
DELETE /campaigns-config/summer2024?hard=true
```

## How It Works

### 1. Campaign Configuration

When you create a campaign configuration, you specify:
- The voucher image template to use
- Default email and SMS templates
- Image base URL for SMS links

### 2. Webhook Processing

When the ManyChat webhook receives a request:

1. **Fetches campaign config** from database
2. **Uses campaign defaults** for templates and image if not provided in request
3. **Generates voucher** using campaign-specific image
4. **Sends email/SMS** using campaign-specific templates

### 3. Request Override

You can still override templates per request:

```json
{
  "campaign": "summer2024",
  "name": "John Doe",
  "phone": "61412345678",
  "email": "john@example.com",
  "city": "Sydney",
  "email_template_id": "override_template_id",
  "sms_template_id": "override_sms_id"
}
```

## Example Setup

### Campaign 1: Summer Promotion

```json
POST /campaigns-config
{
  "campaign": "summer2024",
  "email_template_id": "summer_email_template",
  "sms_template_id": "summer_sms_template",
  "voucher_image_path": "assests/campaigns/summer_voucher.jpg",
  "image_base_url": "http://209.38.84.84/images/"
}
```

### Campaign 2: Birthday Special

```json
POST /campaigns-config
{
  "campaign": "birthday2024",
  "email_template_id": "birthday_email_template",
  "sms_template_id": "birthday_sms_template",
  "voucher_image_path": "assests/campaigns/birthday_voucher.jpg",
  "image_base_url": "http://209.38.84.84/images/"
}
```

## Voucher Image Requirements

- **Format**: JPG or PNG
- **Path**: Relative to project root or absolute path
- **Location**: Store campaign images in `assests/campaigns/` or your preferred location
- **Example**: `assests/campaigns/summer2024_voucher.jpg`

The system will:
1. Use the campaign-specific image if it exists
2. Fall back to default `assests/voucher.jpg` if campaign image not found
3. Log an error if no image is available

## Image Base URL

The `image_base_url` is used to construct the SMS image link:

- If `image_base_url` = `"http://209.38.84.84/images/"`
- Voucher code = `"A7B9C2"`
- Final SMS image URL = `"http://209.38.84.84/images/voucher_A7B9C2.jpg"`

## Error Handling

- **Campaign not found**: Returns 400 error when webhook tries to use unconfigured campaign
- **Image not found**: Falls back to default image or logs error
- **Missing required fields**: Returns 400 error with details

## Best Practices

1. **Create campaign config first** before sending webhook requests
2. **Use descriptive campaign names** (e.g., "summer2024", "birthday2024")
3. **Store campaign images** in organized folders (e.g., `assests/campaigns/`)
4. **Test image paths** before deploying
5. **Use active flag** to temporarily disable campaigns without deleting

