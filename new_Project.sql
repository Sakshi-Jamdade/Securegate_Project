create database project;
SHOW DATABASES;
USE project;
SHOW TABLES;

SELECT * FROM admin;

CREATE TABLE admin (
    id VARCHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    whatsapp VARCHAR(15) NOT NULL,
    password VARCHAR(255) NOT NULL,
    admin_key VARCHAR(10) NOT NULL
);


DESC guard;
SELECT * FROM guard;

CREATE TABLE guard (
    id VARCHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    whatsapp VARCHAR(15) NOT NULL,
    password VARCHAR(255) NOT NULL
);

SELECT * FROM flat_owner;

CREATE TABLE flat_owner (
    id VARCHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    whatsapp VARCHAR(15) NOT NULL,
    flat_number VARCHAR(10) NOT NULL,
    password VARCHAR(255) NOT NULL
);

SELECT * FROM visitors;

-- pre_approved_count-- 
SELECT COUNT(*) AS pre_approved_count
FROM visitors
WHERE status = 'pre-approved';

-- active_visitors_count-- 
SELECT COUNT(*) AS active_visitors_count
FROM visitors
WHERE status = 'approved' AND exit_time IS NULL;

-- todays_visitors_count-- 
SELECT COUNT(*) AS todays_visitors_count
FROM visitors
WHERE DATE(entry_time) = CURDATE();

-- pending_approvals_count-- 
SELECT COUNT(*) AS pending_approvals_count
FROM visitors
WHERE status = 'pending';

CREATE TABLE visitors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id VARCHAR(10) NOT NULL,  -- ✅ Match flat_owner(id)
    visitor_name VARCHAR(255) NOT NULL,
    contact_number VARCHAR(15) NOT NULL,
    purpose VARCHAR(255) NOT NULL,
    entry_time DATETIME,
    exit_time DATETIME,
    expected_date DATETIME,
    additional_notes TEXT,
    status ENUM('pending', 'pre-approved', 'approved', 'denied', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES flat_owner(id) ON DELETE CASCADE
);
ALTER TABLE visitors ADD COLUMN id_proof VARCHAR(255) NULL;

CREATE TABLE family_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id VARCHAR(3),
    name VARCHAR(100) NOT NULL,
    relationship VARCHAR(50) NOT NULL,
    contact VARCHAR(15),
    email VARCHAR(100),
    id_type VARCHAR(50),
    id_number VARCHAR(50),
    photo VARCHAR(255),
    id_proof VARCHAR(255),
    FOREIGN KEY (owner_id) REFERENCES flat_owner(id) ON DELETE CASCADE
);


-- CREATE TABLE visitor_logs (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     visitor_id INT,
--     entry_time DATETIME NOT NULL,
--     exit_time DATETIME NULL,
--     security_guard_id INT,
--     FOREIGN KEY (visitor_id) REFERENCES visitors(id) ON DELETE CASCADE
-- );

