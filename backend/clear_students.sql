-- Clear all students except demo account
-- Step 1: Delete student_verification records for non-demo students
DELETE FROM student_verification 
WHERE student_id IN (
    SELECT id FROM students WHERE enrollment_number != 'DEMO2026001'
);

-- Step 2: Get user_ids of non-demo students to delete later
-- (Store these for reference)
SELECT user_id FROM students WHERE enrollment_number != 'DEMO2026001';

-- Step 3: Delete non-demo students
DELETE FROM students WHERE enrollment_number != 'DEMO2026001';

-- Step 4: Delete associated user accounts (exclude demo user with id=2)
DELETE FROM users WHERE role_id = 1 AND id NOT IN (
    SELECT user_id FROM students
) AND id != 2;

-- Verify remaining students
SELECT * FROM students;
