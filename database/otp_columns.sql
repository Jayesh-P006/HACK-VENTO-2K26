-- OTP columns for email verification
-- Adds columns to student_verification and admin_verification

ALTER TABLE student_verification ADD COLUMN otp VARCHAR(6);
ALTER TABLE student_verification ADD COLUMN otp_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE student_verification ADD COLUMN otp_sent_at DATETIME;
ALTER TABLE student_verification ADD COLUMN otp_verified_at DATETIME;
ALTER TABLE student_verification ADD COLUMN otp_attempts INT DEFAULT 0;

ALTER TABLE admin_verification ADD COLUMN otp VARCHAR(6);
ALTER TABLE admin_verification ADD COLUMN otp_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE admin_verification ADD COLUMN otp_sent_at DATETIME;
ALTER TABLE admin_verification ADD COLUMN otp_verified_at DATETIME;
ALTER TABLE admin_verification ADD COLUMN otp_attempts INT DEFAULT 0;
