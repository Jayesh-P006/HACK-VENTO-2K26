# Admin (TPO) Dashboard - API Documentation

## Overview
The Admin Dashboard is a comprehensive management control hub for Placement & Internship Portal administrators (TPOs). It provides tools for student verification, blacklist management, master data administration, analytics, and reporting.

**Base URL:** `http://localhost:5000/api/admin`

All endpoints require JWT authentication with `role_id = 3` (Admin).

---

## Database Schema

### 1. **student_verification** (11 columns)
Document verification queue for newly registered students.

```
id              | INT (Primary Key)
student_id      | INT (Foreign Key → students.id, UNIQUE)
status          | ENUM ('Pending', 'Verified', 'Rejected') [DEFAULT: 'Pending']
marksheet_10th_url    | VARCHAR(500)
marksheet_12th_url    | VARCHAR(500)
degree_certificate_url | VARCHAR(500)
verification_date     | DATETIME
rejection_reason      | TEXT
verified_by     | INT (Foreign Key → users.id)
submitted_at    | DATETIME [DEFAULT: NOW()]
updated_at      | DATETIME [DEFAULT: NOW()]
```

**Purpose:** Track document verification status of students. Once verified, they can apply for drives.

---

### 2. **student_blacklist** (10 columns)
Disciplinary freeze list for students.

```
id              | INT (Primary Key)
student_id      | INT (Foreign Key → students.id, UNIQUE)
is_blacklisted  | BOOLEAN [DEFAULT: FALSE]
reason          | TEXT
severity        | ENUM ('Low', 'Medium', 'High', 'Critical') [DEFAULT: 'Medium']
blacklisted_by  | INT (Foreign Key → users.id)
blacklisted_date | DATETIME [DEFAULT: NOW()]
unblacklist_date | DATETIME (NULL for permanent)
created_at      | DATETIME [DEFAULT: NOW()]
updated_at      | DATETIME [DEFAULT: NOW()]
```

**Purpose:** Prevent account access for discipline violations (not showing up for interviews, etc.).

---

### 3. **departments** (8 columns)
Master list of departments/branches.

```
id              | INT (Primary Key)
name            | VARCHAR(100) [UNIQUE]
code            | VARCHAR(10) [UNIQUE]
description     | TEXT
total_students  | INT [DEFAULT: 0]
is_active       | BOOLEAN [DEFAULT: TRUE]
created_at      | DATETIME [DEFAULT: NOW()]
updated_at      | DATETIME [DEFAULT: NOW()]
```

**Example Data:**
- CSE, Computer Science & Engineering
- IT, Information Technology
- ECE, Electronics & Communication

---

### 4. **batch_years** (7 columns)
Master list of graduation batches.

```
id              | INT (Primary Key)
year            | INT [UNIQUE]
academic_session | VARCHAR(20)
total_students  | INT [DEFAULT: 0]
is_active       | BOOLEAN [DEFAULT: TRUE]
created_at      | DATETIME [DEFAULT: NOW()]
updated_at      | DATETIME [DEFAULT: NOW()]
```

**Example:** Year: 2024, Academic Session: "2024-2025"

---

### 5. **skills** (7 columns)
Master list of technical skills.

```
id              | INT (Primary Key)
name            | VARCHAR(100) [UNIQUE]
category        | VARCHAR(50)
description     | TEXT
is_active       | BOOLEAN [DEFAULT: TRUE]
created_at      | DATETIME [DEFAULT: NOW()]
updated_at      | DATETIME [DEFAULT: NOW()]
```

**Categories:** Programming, Framework, Database, Cloud, DevOps, Other

---

### 6. **placement_stats** (11 columns)
Aggregated placement statistics for analytics.

```
id              | INT (Primary Key)
date            | DATE [UNIQUE]
total_students  | INT [DEFAULT: 0]
placed_students | INT [DEFAULT: 0]
unplaced_students | INT [DEFAULT: 0]
highest_package | DECIMAL(12,2) [DEFAULT: 0]
average_package | DECIMAL(12,2) [DEFAULT: 0]
department_stats | JSON
total_companies_visiting | INT [DEFAULT: 0]
companies_in_interview   | INT [DEFAULT: 0]
created_at      | DATETIME [DEFAULT: NOW()]
updated_at      | DATETIME [DEFAULT: NOW()]
```

**Department Stats JSON Example:**
```json
{
  "CSE": {"placed": 50, "total": 80, "placement_rate": 62.5},
  "IT": {"placed": 35, "total": 60, "placement_rate": 58.3}
}
```

---

### 7. **company_visits** (13 columns)
Track company visit schedules and status.

```
id              | INT (Primary Key)
job_id          | INT (Foreign Key → jobs.id)
company_id      | INT (Foreign Key → companies.id)
visit_date      | DATETIME
status          | ENUM ('Scheduled', 'Interview Stage', 'Offer Stage', 'Completed', 'Cancelled')
location        | VARCHAR(255)
interview_type  | ENUM ('Online', 'Onsite', 'Hybrid') [DEFAULT: 'Online']
total_applications | INT [DEFAULT: 0]
shortlisted_count | INT [DEFAULT: 0]
selected_count  | INT [DEFAULT: 0]
notes           | TEXT
created_at      | DATETIME [DEFAULT: NOW()]
updated_at      | DATETIME [DEFAULT: NOW()]
```

---

## API Endpoints

### **VERIFICATION QUEUE**

#### 1. Get Verification Queue
```
GET /api/admin/verification-queue?page=1&per_page=20&status=Pending
```

**Parameters:**
- `page` (int): Page number for pagination
- `per_page` (int): Records per page (default: 20)
- `status` (string): Filter by status - 'All', 'Pending', 'Verified', 'Rejected'

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "student_id": 1,
      "student_name": "John Doe",
      "enrollment_number": "21CS001",
      "branch": "CSE",
      "status": "Pending",
      "rejection_reason": null,
      "submitted_at": "2024-01-15T10:30:00"
    }
  ],
  "pagination": {
    "total": 45,
    "pages": 3,
    "current_page": 1,
    "per_page": 20
  }
}
```

---

#### 2. Approve Student Verification
```
POST /api/admin/verification/<verification_id>/approve
```

**Response:**
```json
{
  "success": true,
  "message": "Student John Doe verified successfully"
}
```

**Action:** Marks student as verified and activates their user account.

---

#### 3. Reject Student Verification
```
POST /api/admin/verification/<verification_id>/reject
Content-Type: application/json

{
  "rejection_reason": "Mark sheets clarity is poor"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Student John Doe rejected"
}
```

---

### **BLACKLIST MANAGEMENT**

#### 1. Get Blacklisted Students
```
GET /api/admin/blacklist/students
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "student_id": 5,
      "student_name": "Jane Smith",
      "is_blacklisted": true,
      "reason": "No-show in interview with Infosys",
      "severity": "High",
      "blacklisted_date": "2024-01-20T14:00:00",
      "unblacklist_date": "2024-03-20T14:00:00"
    }
  ]
}
```

---

#### 2. Blacklist a Student
```
POST /api/admin/blacklist/add
Content-Type: application/json

{
  "student_id": 5,
  "reason": "No-show in interview with Infosys",
  "severity": "High",
  "duration_days": 60
}
```

**Parameters:**
- `student_id` (int): Required
- `reason` (string): Required
- `severity` (string): 'Low', 'Medium', 'High', 'Critical'
- `duration_days` (int): Leave blank for permanent blacklist

**Response:**
```json
{
  "success": true,
  "message": "Student blacklisted successfully",
  "data": { /* blacklist record */ }
}
```

---

#### 3. Remove from Blacklist
```
POST /api/admin/blacklist/remove/<blacklist_id>
```

**Response:**
```json
{
  "success": true,
  "message": "Student removed from blacklist"
}
```

---

### **MASTER DATA MANAGEMENT**

#### DEPARTMENTS

**Get All Departments:**
```
GET /api/admin/departments
```

**Add Department:**
```
POST /api/admin/departments
Content-Type: application/json

{
  "code": "CSE",
  "name": "Computer Science & Engineering",
  "description": "Core CS department"
}
```

**Update Department:**
```
PUT /api/admin/departments/<dept_id>
Content-Type: application/json

{
  "name": "Computer Science & Engineering",
  "description": "Updated description",
  "is_active": true
}
```

---

#### BATCH YEARS

**Get All Batch Years:**
```
GET /api/admin/batch-years
```

**Add Batch Year:**
```
POST /api/admin/batch-years
Content-Type: application/json

{
  "year": 2024,
  "academic_session": "2024-2025"
}
```

---

#### SKILLS

**Get All Skills:**
```
GET /api/admin/skills
```

**Add Skill:**
```
POST /api/admin/skills
Content-Type: application/json

{
  "name": "React",
  "category": "Framework",
  "description": "React JS library"
}
```

---

### **ANALYTICS & INSIGHTS**

#### 1. Placement Statistics
```
GET /api/admin/analytics/placement-stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "date": "2024-01-20",
    "total_students": 200,
    "placed_students": 120,
    "unplaced_students": 80,
    "placement_rate": 60.0,
    "highest_package": 24.50,
    "average_package": 14.75,
    "department_stats": {
      "CSE": {"placed": 50, "total": 80, "placement_rate": 62.5},
      "IT": {"placed": 35, "total": 60, "placement_rate": 58.3}
    },
    "total_companies_visiting": 15,
    "companies_in_interview": 8
  }
}
```

---

#### 2. Company Visits
```
GET /api/admin/analytics/company-visits
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "company_name": "Wipro",
      "company_logo": "url...",
      "job_title": "Software Engineer",
      "visit_date": "2024-01-25T10:00:00",
      "status": "Interview Stage",
      "location": "Campus",
      "interview_type": "Onsite",
      "total_applications": 150,
      "shortlisted_count": 45,
      "selected_count": 12
    }
  ]
}
```

---

#### 3. Check Scheduling Conflicts
```
GET /api/admin/analytics/conflict-check
```

**Response:**
```json
{
  "success": true,
  "conflicts_found": true,
  "conflicts": [
    {
      "company1": "Wipro",
      "company2": "Infosys",
      "scheduled_date": "2024-01-25T10:00:00",
      "severity": "Critical"
    }
  ]
}
```

---

#### 4. Department-wise Statistics
```
GET /api/admin/analytics/department-stats
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "department": "CSE",
      "total_students": 80,
      "placed": 50,
      "unplaced": 30,
      "placement_rate": 62.5
    }
  ]
}
```

---

### **REPORTS & EXPORT**

#### 1. Export Student Data (CSV)
```
GET /api/admin/reports/student-data
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "enrollment_number": "21CS001",
      "full_name": "John Doe",
      "email": "john@example.com",
      "branch": "CSE",
      "cgpa": 8.5,
      "graduation_year": 2024,
      "is_placed": "Yes",
      "profile_completed": "Yes"
    }
  ],
  "total_records": 200
}
```

---

#### 2. Generate Placement Report
```
GET /api/admin/reports/placement-report
```

**Response:**
```json
{
  "success": true,
  "report": {
    "timestamp": "2024-01-20T15:30:00",
    "total_students": 200,
    "placed_students": 120,
    "unplaced_students": 80,
    "placement_rate": 60.0,
    "highest_package": 24.50,
    "average_package": 14.75,
    "total_companies": 15,
    "department_breakdown": [
      {
        "department": "CSE",
        "total": 80,
        "placed": 50,
        "rate": 62.5
      }
    ]
  }
}
```

---

## Features Summary

### 1. **Verification Queue**
- View pending student document verifications
- Server-side pagination (up to 2000+ records)
- Approve/Reject with comments
- Auto-activates verified student accounts

### 2. **Blacklist Management**
- Add students to blacklist with severity levels
- Temporary (duration-based) or permanent blacklist
- Auto-unlock on expiry
- Prevents blacklisted students from applying

### 3. **Master Data Management**
- CRUD operations for:
  - Departments (CSE, IT, ECE, etc.)
  - Batch Years (2023-2024, 2024-2025, etc.)
  - Skills (Python, React, AWS, etc.)

### 4. **Analytics Dashboard**
- **Placement Stats:** Placed vs. Unplaced with percentage
- **Package Analytics:** Highest, Average, Distribution
- **Department Breakdown:** Placement rate by department
- **Company Visits:** Current status of company recruitment drives
- **Conflict Detection:** Alert for overlapping company visits

### 5. **Reports & Export**
- Export student data to CSV
- Generate comprehensive placement reports
- Department-wise analytics
- All data exportable for Excel/PDF

---

## Security & Validation

✓ JWT Authentication required (Admin role only)  
✓ Server-side pagination (prevent data dumps)  
✓ Database constraints (unique fields, foreign keys)  
✓ Status validation (enum fields)  
✓ Auto-rollback on transaction errors  

---

## Access

**Dashboard URL:** `http://localhost:3000/admin-dashboard.html`

**Demo Credentials:**
- Email: `admin@tpo.edu` (create in database)
- Password: `password123`
- Role: Admin (3)

---

## Performance Optimization

- **Pagination:** Server-side pagination for 2000+ students
- **Aggregation:** Pre-calculated placement stats
- **Indexing:** Foreign key indexes on common queries
- **Batch Operations:** Bulk import/export capabilities

---

## Future Enhancements

- [ ] Bulk student import from Excel
- [ ] Email notifications for verification approvals
- [ ] Custom report generation
- [ ] Advanced filtering and search
- [ ] Dashboard analytics caching
- [ ] Audit logging for admin actions

