-- Database schema for Birthday Voucher application
-- Normalized 3-table structure

-- Create database (uncomment if needed)
-- CREATE DATABASE IF NOT EXISTS birthday_vouchers CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE birthday_vouchers;

-- 1. Customer table - stores customer information
CREATE TABLE IF NOT EXISTS customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    birthday INT,
    birth_month INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_phone (phone),
    INDEX idx_birthday (birth_month, birthday)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Vouchers table - stores voucher information linked to customers
CREATE TABLE IF NOT EXISTS vouchers (
    voucher_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    year INT NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    status ENUM('active', 'redeemed', 'expired') NOT NULL DEFAULT 'active',
    issued_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE,
    INDEX idx_customer_id (customer_id),
    INDEX idx_code (code),
    INDEX idx_year (year),
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at),
    UNIQUE KEY unique_customer_year (customer_id, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Voucher redemptions table - tracks when/where vouchers are redeemed
CREATE TABLE IF NOT EXISTS voucher_redemptions (
    redemption_id INT AUTO_INCREMENT PRIMARY KEY,
    voucher_id INT NOT NULL,
    redeemed_location VARCHAR(255),
    redeemed_at DATETIME NOT NULL,
    FOREIGN KEY (voucher_id) REFERENCES vouchers(voucher_id) ON DELETE CASCADE,
    INDEX idx_voucher_id (voucher_id),
    INDEX idx_redeemed_at (redeemed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
