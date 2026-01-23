-- Migration script to update existing manychat_vouchers table to support campaigns
-- Run this script if you already have the manychat_vouchers table without campaign support

-- Step 1: Add campaign column (set default for existing records)
ALTER TABLE manychat_vouchers 
ADD COLUMN campaign VARCHAR(100) NOT NULL DEFAULT 'default' AFTER id;

-- Step 2: Add email_template_id and sms_template_id columns
ALTER TABLE manychat_vouchers 
ADD COLUMN email_template_id VARCHAR(100) AFTER issue_date,
ADD COLUMN sms_template_id VARCHAR(100) AFTER email_template_id;

-- Step 3: Drop the old unique constraint on email
ALTER TABLE manychat_vouchers 
DROP INDEX email;

-- Step 4: Add new composite unique constraint (campaign + email)
ALTER TABLE manychat_vouchers 
ADD UNIQUE KEY unique_campaign_email (campaign, email);

-- Step 5: Add indexes for better query performance
ALTER TABLE manychat_vouchers 
ADD INDEX idx_campaign (campaign),
ADD INDEX idx_campaign_voucher (campaign, voucher_code);

-- Step 6: Remove the default value from campaign column (optional, after setting proper values)
-- ALTER TABLE manychat_vouchers ALTER COLUMN campaign DROP DEFAULT;

