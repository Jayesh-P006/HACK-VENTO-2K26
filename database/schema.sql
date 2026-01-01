-- Placement and Internship Management Portal Database Schema
-- MySQL Database

CREATE DATABASE IF NOT EXISTS placement_portal;
USE placement_portal;

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS announcements;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;

-- Users Table (Centralized Authentication)
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id TINYINT NOT NULL COMMENT '1=Student, 2=Company, 3=Admin',
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role_id)
);

-- Students Table (Profile Details)
CREATE TABLE students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    enrollment_number VARCHAR(50) UNIQUE NOT NULL,
    branch VARCHAR(100) NOT NULL,
    cgpa DECIMAL(3,2) NOT NULL,
    tenth_percentage DECIMAL(5,2),
    twelfth_percentage DECIMAL(5,2),
    graduation_year INT NOT NULL,
    phone VARCHAR(15),
    resume_url VARCHAR(500),
    ats_score INT,
    ats_feedback TEXT,
    ats_calculated_at TIMESTAMP NULL,
    skills TEXT,
    experience TEXT,
    projects TEXT,
    certifications TEXT,
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    profile_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_cgpa (cgpa),
    INDEX idx_branch (branch)
);

-- Companies Table (Recruiter Profile)
CREATE TABLE companies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    hr_name VARCHAR(255) NOT NULL,
    hr_phone VARCHAR(15),
    company_website VARCHAR(255),
    logo_url VARCHAR(500),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_company_name (company_name)
);

-- Jobs Table
CREATE TABLE jobs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    job_type ENUM('Internship', 'Full-Time', 'Part-Time') NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT,
    location VARCHAR(255),
    salary_range VARCHAR(100),
    min_cgpa DECIMAL(3,2) DEFAULT 0.00,
    min_10th_percentage DECIMAL(5,2) DEFAULT NULL,
    min_12th_percentage DECIMAL(5,2) DEFAULT NULL,
    eligible_branches TEXT COMMENT 'Comma-separated branch names',
    application_deadline DATE NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected', 'Closed') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_deadline (application_deadline),
    INDEX idx_company (company_id)
);

-- Applications Table (Pivot Table)
CREATE TABLE applications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    job_id INT NOT NULL,
    status ENUM('Applied', 'Shortlisted', 'Interview', 'Selected', 'Rejected') DEFAULT 'Applied',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    notes TEXT COMMENT 'Interview feedback or notes',
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    UNIQUE KEY unique_application (student_id, job_id),
    INDEX idx_status (status),
    INDEX idx_student (student_id),
    INDEX idx_job (job_id)
);

-- Announcements Table (Admin Broadcasts)
CREATE TABLE announcements (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    target_role TINYINT COMMENT '1=Student, 2=Company, NULL=All',
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_target (target_role)
);

-- Student Verification Table
CREATE TABLE student_verification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_student (student_id)
);

-- Student Blacklist Table
CREATE TABLE student_blacklist (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    reason TEXT,
    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_student (student_id)
);

-- Create Views for Analytics

-- Placement Statistics View
CREATE VIEW placement_stats AS
SELECT 
    COUNT(DISTINCT s.id) as total_students,
    COUNT(DISTINCT CASE WHEN a.status = 'Selected' THEN s.id END) as placed_students,
    COUNT(DISTINCT j.id) as total_jobs,
    COUNT(DISTINCT c.id) as total_companies
FROM students s
LEFT JOIN applications a ON s.id = a.student_id
LEFT JOIN jobs j ON j.status = 'Approved'
LEFT JOIN companies c ON c.user_id IN (SELECT id FROM users WHERE is_verified = TRUE);

-- Branch-wise Placement View
CREATE VIEW branch_placement AS
SELECT 
    s.branch,
    COUNT(DISTINCT s.id) as total_students,
    COUNT(DISTINCT CASE WHEN a.status = 'Selected' THEN s.id END) as placed_students,
    ROUND(COUNT(DISTINCT CASE WHEN a.status = 'Selected' THEN s.id END) * 100.0 / COUNT(DISTINCT s.id), 2) as placement_percentage
FROM students s
LEFT JOIN applications a ON s.id = a.student_id
GROUP BY s.branch;
