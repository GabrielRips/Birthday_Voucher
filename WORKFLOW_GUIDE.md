# Campaign Workflow Guide

This guide explains the complete workflow for setting up and using campaigns.

## Two-Step Process

### Step 1: Configure Campaign (One-Time Setup)

**First**, you configure the campaign with its templates and voucher image. This is done **once** per campaign and saved to the database.

**Endpoint:** `POST /campaigns-config`

**Request:**
```json
{
  "campaign": "summer2024",
  "email_template_id": "abc123",
  "sms_template_id": "xyz789",
  "voucher_image_path": "assests/campaigns/summer_voucher.jpg",
  "image_base_url": "http://209.38.84.84/images/"
}
```

**What happens:**
- Campaign configuration is **saved to the database** (`campaigns_config` table)
- This includes:
  - Email template ID
  - SMS template ID
  - Voucher image path
  - Image base URL
- This configuration is now **permanently stored** and will be used for all future requests

### Step 2: Use Campaign (ManyChat Webhook)

**Then**, when ManyChat sends webhook requests, you only need to send the user data. The system **automatically pulls** the campaign configuration from the database.

**Endpoint:** `POST /manychat-webhook`

**Request:**
```json
{
  "campaign": "summer2024",
  "name": "John Doe",
  "phone": "61412345678",
  "email": "john@example.com",
  "city": "Sydney"
}
```

**What happens:**
1. System receives the webhook request
2. **Automatically fetches** campaign config from database using `campaign: "summer2024"`
3. Uses the **saved** email template, SMS template, and voucher image
4. Generates voucher with the campaign-specific image
5. Sends email and SMS using the campaign-specific templates

## Complete Example Workflow

### Day 1: Setup Campaign

```bash
# 1. Upload voucher image to server
# File: assests/campaigns/summer_voucher.jpg

# 2. Configure campaign (one-time setup)
POST /campaigns-config
{
  "campaign": "summer2024",
  "email_template_id": "summer_email_123",
  "sms_template_id": "summer_sms_456",
  "voucher_image_path": "assests/campaigns/summer_voucher.jpg",
  "image_base_url": "http://209.38.84.84/images/"
}

# Response: Campaign saved to database ✅
```

### Day 2+: Use Campaign (ManyChat Webhooks)

```bash
# ManyChat sends webhook - you only send user data
POST /manychat-webhook
{
  "campaign": "summer2024",
  "name": "Jane Smith",
  "phone": "61412345678",
  "email": "jane@example.com",
  "city": "Melbourne"
}

# System automatically:
# ✅ Looks up "summer2024" in database
# ✅ Uses saved email template "summer_email_123"
# ✅ Uses saved SMS template "summer_sms_456"
# ✅ Uses saved image "assests/campaigns/summer_voucher.jpg"
# ✅ Generates voucher and sends ✅
```

## Key Points

1. **One-Time Setup**: Configure campaign once, use many times
2. **Automatic Lookup**: System automatically pulls campaign config from database
3. **No Repeated Data**: You don't need to send templates/images in every webhook request
4. **Easy Management**: Update campaign config anytime via `/campaigns-config` endpoint

## Updating Campaign Configuration

If you need to change templates or images later:

```bash
# Update campaign config (same endpoint, just change values)
POST /campaigns-config
{
  "campaign": "summer2024",
  "email_template_id": "new_summer_email_789",  # Changed
  "sms_template_id": "summer_sms_456",
  "voucher_image_path": "assests/campaigns/new_summer_voucher.jpg",  # Changed
  "image_base_url": "http://209.38.84.84/images/"
}

# All future webhook requests will use the new config ✅
```

## Optional: Override Per Request

You can still override templates for specific requests if needed:

```json
POST /manychat-webhook
{
  "campaign": "summer2024",
  "name": "John Doe",
  "phone": "61412345678",
  "email": "john@example.com",
  "city": "Sydney",
  "email_template_id": "special_template",  # Override saved template
  "sms_template_id": "special_sms"         # Override saved template
}
```

## Summary

**Setup (Once):**
1. Upload voucher image
2. POST to `/campaigns-config` with campaign details
3. Configuration saved to database ✅

**Usage (Many Times):**
1. POST to `/manychat-webhook` with just `campaign` + user data
2. System automatically uses saved campaign config ✅
3. Voucher generated and sent ✅

No need to send templates/images in every webhook request - they're stored in the database!

