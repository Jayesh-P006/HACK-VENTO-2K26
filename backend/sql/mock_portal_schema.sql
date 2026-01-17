-- Mock portal schema (MySQL 8+) for seed_mock_portal_data.py
-- Creates the minimal tables needed for mock Users/Students/Companies/StudentVerification.

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(255) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `role_id` SMALLINT NOT NULL COMMENT '1=Student, 2=Company, 3=Admin',
  `is_verified` BOOLEAN NOT NULL DEFAULT FALSE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `batches` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `batch_code` VARCHAR(50) NOT NULL,
  `start_year` INT NOT NULL,
  `end_year` INT NOT NULL,
  `degree` VARCHAR(100) NOT NULL,
  `program` VARCHAR(100) NULL,
  `description` TEXT NULL,
  `status` ENUM('Active','Graduated','Archived') NOT NULL DEFAULT 'Active',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_batches_batch_code` (`batch_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `students` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `full_name` VARCHAR(255) NOT NULL,
  `enrollment_number` VARCHAR(50) NOT NULL,
  `branch` VARCHAR(100) NOT NULL,
  `cgpa` DECIMAL(3,2) NOT NULL,
  `tenth_percentage` DECIMAL(5,2) NULL,
  `twelfth_percentage` DECIMAL(5,2) NULL,
  `graduation_year` INT NOT NULL,
  `batch_id` INT NULL,
  `current_year` SMALLINT NULL,
  `phone` VARCHAR(15) NULL,
  `resume_url` VARCHAR(500) NULL,

  `resume_storage_provider` ENUM('local','drive') NOT NULL DEFAULT 'local',
  `resume_filename` VARCHAR(255) NULL,
  `resume_drive_file_id` VARCHAR(128) NULL,
  `resume_drive_web_view_link` VARCHAR(500) NULL,
  `resume_updated_at` DATETIME NULL,

  `ats_score` INT NULL,
  `ats_feedback` TEXT NULL,
  `ats_calculated_at` DATETIME NULL,

  `skills` TEXT NULL,
  `experience` TEXT NULL,
  `projects` TEXT NULL,
  `certifications` TEXT NULL,
  `linkedin_url` VARCHAR(500) NULL,
  `github_url` VARCHAR(500) NULL,
  `profile_completed` BOOLEAN NOT NULL DEFAULT FALSE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_students_user_id` (`user_id`),
  UNIQUE KEY `uq_students_enrollment_number` (`enrollment_number`),
  KEY `idx_students_batch_id` (`batch_id`),
  CONSTRAINT `fk_students_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_students_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `companies` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `company_name` VARCHAR(255) NOT NULL,
  `industry` VARCHAR(100) NULL,
  `hr_name` VARCHAR(255) NOT NULL,
  `hr_phone` VARCHAR(15) NULL,
  `company_website` VARCHAR(255) NULL,
  `logo_url` VARCHAR(500) NULL,
  `description` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_companies_user_id` (`user_id`),
  CONSTRAINT `fk_companies_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `student_verification` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `student_id` INT NOT NULL,
  `status` ENUM('Pending','Verified','Rejected') NOT NULL DEFAULT 'Pending',

  `otp` VARCHAR(6) NULL,
  `otp_verified` BOOLEAN NOT NULL DEFAULT FALSE,
  `otp_sent_at` DATETIME NULL,
  `otp_verified_at` DATETIME NULL,
  `otp_attempts` INT NOT NULL DEFAULT 0,

  `marksheet_10th_url` VARCHAR(500) NULL,
  `marksheet_12th_url` VARCHAR(500) NULL,
  `degree_certificate_url` VARCHAR(500) NULL,
  `verification_date` DATETIME NULL,
  `rejection_reason` TEXT NULL,
  `verified_by` INT NULL,

  `submitted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_student_verification_student_id` (`student_id`),
  KEY `idx_student_verification_verified_by` (`verified_by`),
  CONSTRAINT `fk_student_verification_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_student_verification_admin` FOREIGN KEY (`verified_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
