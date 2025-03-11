use securegate_db;

select *from admin;
CREATE TABLE admin (
    id VARCHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    whatsapp VARCHAR(15) NOT NULL,
    password VARCHAR(255) NOT NULL,
    admin_key VARCHAR(10) NOT NULL
);


DESC guard;
select *from guard;
CREATE TABLE guard (
    id VARCHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    whatsapp VARCHAR(15) NOT NULL,
    password VARCHAR(255) NOT NULL
);
delete from guard where email="sakshijamdade2020@gmail.com";

select *from flat_owner;
CREATE TABLE flat_owner (
    id VARCHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    whatsapp VARCHAR(15) NOT NULL,
    flat_number VARCHAR(10) NOT NULL,
    password VARCHAR(255) NOT NULL
);


CREATE TABLE family_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id VARCHAR(3),
    name VARCHAR(100) NOT NULL,
    relationship VARCHAR(50) NOT NULL,
    contact VARCHAR(15),
    email VARCHAR(100) ,
    FOREIGN KEY (owner_id) REFERENCES flat_owner(id) ON DELETE CASCADE
);

-- ALTER TABLE family_members 
-- ADD COLUMN email VARCHAR(100) NOT NULL;


INSERT INTO family_members (owner_id, name, relationship, contact) VALUES
('F01', 'Jane Doe', 'Daughter', '9123456789'),
('F01', 'Michael Doe', 'Son', '9234567890');

SELECT * FROM family_members;
delete from family_members where id="15"; 

select *from visitors;
CREATE TABLE visitors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id VARCHAR(3),
    visitor_name VARCHAR(100) NOT NULL,
    contact VARCHAR(15),
    purpose VARCHAR(255),
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP NULL,
    status ENUM('pre-approved', 'pending', 'checked-in', 'checked-out') DEFAULT 'pending',
    FOREIGN KEY (owner_id) REFERENCES flat_owner(id) ON DELETE CASCADE
);

INSERT INTO visitors (owner_id, visitor_name, contact, purpose, status, entry_time) VALUES
('F01', 'David Lee', '9988776655', 'Meeting', 'pre-approved', NOW()),
('F01', 'Alice Brown', '9776655443', 'Package Delivery', 'pending', NOW()),
('F01', 'Robert Williams', '9654321987', 'Friend Visit', 'checked-in', NOW());
