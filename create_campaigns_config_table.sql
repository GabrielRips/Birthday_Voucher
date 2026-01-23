-- SQL script to create the campaigns_config table
-- This table stores default email/SMS templates and voucher images for each campaign

CREATE TABLE IF NOT EXISTS campaigns_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign VARCHAR(100) NOT NULL UNIQUE,
    email_template_id VARCHAR(100),
    sms_template_id VARCHAR(100),
    voucher_image_path VARCHAR(500) NOT NULL COMMENT 'Path to the base voucher image (JPG/PNG)',
    image_base_url VARCHAR(500) COMMENT 'Base URL for voucher images (e.g., http://209.38.84.84/images/)',
    active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_campaign (campaign),
    INDEX idx_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

