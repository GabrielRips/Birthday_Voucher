-- SQL script to create the manychat_vouchers table
-- Run this script in your MySQL database to create the table for ManyChat voucher data
-- Optimized to support multiple campaigns with different vouchers

CREATE TABLE IF NOT EXISTS manychat_vouchers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    city VARCHAR(255),
    voucher_code VARCHAR(50) NOT NULL,
    issue_date DATE NOT NULL,
    email_template_id VARCHAR(100),
    sms_template_id VARCHAR(100),
    email_sent TINYINT(1) DEFAULT 0,
    sms_sent TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Unique constraint: same email can be used in different campaigns
    UNIQUE KEY unique_campaign_email (campaign, email),
    INDEX idx_campaign (campaign),
    INDEX idx_email (email),
    INDEX idx_voucher_code (voucher_code),
    INDEX idx_campaign_voucher (campaign, voucher_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

