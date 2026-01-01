# Company Dashboard - Advanced Features Guide

## Overview
The upgraded Company Dashboard provides comprehensive tools for recruiting, managing applicants, scheduling interviews, and generating offer letters. This guide covers all new features and their implementation.

---

## 1. CREATE DRIVE WIZARD (3-Step Form)

### Features
Multi-step intelligent form to post jobs with complex eligibility criteria and hiring process configuration.

### Step 1: Job Details
**Fields:**
- Job Title *
- Job Type (Full-Time, Internship, Part-Time)
- Location *
- CTC *
- Description *
- Requirements
- Application Deadline *

**API Endpoint:**
```
POST /api/company/create-drive/step1
{
  "title": "Senior Software Engineer",
  "job_type": "Full-Time",
  "location": "Bangalore",
  "ctc": "18-25 LPA",
  "description": "...",
  "requirements": "...",
  "application_deadline": "2026-03-31"
}

Response: { "job_id": 1, "step": 1 }
```

### Step 2: Eligibility Criteria
**Fields:**
- Minimum CGPA
- Minimum 10th Percentage
- Minimum 12th Percentage
- Eligible Branches (Multi-select: CSE, IT, ECE, ME, CE, etc.)

**API Endpoint:**
```
POST /api/company/create-drive/{job_id}/step2
{
  "min_cgpa": 8.0,
  "eligible_branches": ["CSE", "IT"],
  "min_10th_percentage": 75,
  "min_12th_percentage": 80
}

Response: { "job_id": 1, "step": 2 }
```

**Database Schema:**
```sql
-- Job table enhancements
ALTER TABLE jobs ADD COLUMN min_10th_percentage DECIMAL(5,2);
ALTER TABLE jobs ADD COLUMN min_12th_percentage DECIMAL(5,2);
-- eligible_branches stores JSON array: ["CSE", "IT"]
```

### Step 3: Hiring Process Configuration
**Define Multiple Rounds:**
- Round Type (Aptitude Test, Group Discussion, Technical Interview, HR Interview)
- Duration (minutes)
- Description

**API Endpoint:**
```
POST /api/company/create-drive/{job_id}/step3
{
  "rounds": [
    {
      "type": "Aptitude Test",
      "description": "General aptitude assessment",
      "duration_minutes": 60
    },
    {
      "type": "Technical Interview",
      "description": "1-on-1 technical discussion",
      "duration_minutes": 45
    },
    {
      "type": "HR Interview",
      "description": "HR and culture fit discussion",
      "duration_minutes": 30
    }
  ]
}

Response: { "job_id": 1, "step": 3, "total_rounds": 3 }
```

**New Tables:**
```sql
CREATE TABLE hiring_rounds (
  id INT PRIMARY KEY,
  job_id INT FOREIGN KEY,
  round_number INT,
  round_type VARCHAR(50),
  description TEXT,
  duration_minutes INT,
  created_at TIMESTAMP
);

CREATE TABLE application_rounds (
  id INT PRIMARY KEY,
  application_id INT FOREIGN KEY,
  hiring_round_id INT FOREIGN KEY,
  status ENUM('Pending', 'Scheduled', 'Completed', 'Passed', 'Failed'),
  score DECIMAL(5,2),
  feedback TEXT,
  completed_at TIMESTAMP
);
```

---

## 2. ADVANCED APPLICANT MANAGEMENT

### A. Smart Filtering & Data Grid

**Features:**
- Filter by CGPA
- Filter by Branch
- Filter by Application Status
- **SMART: "Hide Ineligible Candidates"** - Auto-filters based on job eligibility criteria

**API Endpoint:**
```
GET /api/company/job/{job_id}/applicants/advanced?hide_ineligible=true&min_cgpa=8.0&branch=CSE&status=Shortlisted

Response:
{
  "total": 45,
  "applicants": [
    {
      "application_id": 123,
      "student_id": 456,
      "name": "Rajesh Kumar",
      "enrollment": "21BIT001",
      "branch": "CSE",
      "cgpa": 8.5,
      "phone": "9876543210",
      "skills": "Python, JavaScript, React",
      "status": "Applied",
      "applied_at": "2026-01-15T10:30:00",
      "eligible": true,
      "ineligibility_reasons": []
    },
    {
      "application_id": 124,
      "eligible": false,
      "ineligibility_reasons": [
        "CGPA 7.2 below minimum 8.0",
        "Branch IT not in eligible branches: [CSE]"
      ]
    }
  ],
  "filters_applied": {
    "hide_ineligible": true,
    "sort_by": "cgpa",
    "sort_order": "desc"
  }
}
```

### B. Bulk Download Resumes as ZIP

**Features:**
- Select multiple applicants
- Download all resumes as single ZIP file
- Includes: name, email, phone, branch, CGPA, skills

**API Endpoint:**
```
POST /api/company/job/{job_id}/applicants/download-resumes
{
  "student_ids": [456, 789, 1011]
}

Response: { "message": "ZIP created with 3 resumes", "count": 3 }
```

**File Structure in ZIP:**
```
Rajesh_Kumar_21BIT001_resume.txt
Priya_Sharma_21BIT002_resume.txt
Amit_Singh_21BIT003_resume.txt
```

### C. Bulk Status Upload (CSV/Excel)

**Features:**
- Upload CSV/Excel with columns: `student_id`, `status`
- Update application statuses in bulk
- Error reporting for invalid rows

**API Endpoint:**
```
POST /api/company/job/{job_id}/bulk-status-upload
Content-Type: multipart/form-data

File format (CSV):
student_id,status
456,Shortlisted
789,Interview
1011,Selected
1213,Rejected

Response:
{
  "message": "Bulk status update completed",
  "updated_count": 3,
  "error_count": 1,
  "errors": [
    "Row 5: Invalid status 'Pending'"
  ]
}
```

---

## 3. INTERVIEW SCHEDULING SYSTEM

### A. Create Interview Slots

**Features:**
- Define available time slots per hiring round
- Set capacity (max candidates per slot)
- Configure for online (meeting link) or onsite (location) interviews

**API Endpoint:**
```
POST /api/company/job/{job_id}/interview-slots
{
  "hiring_round_id": 5,
  "slots": [
    {
      "date": "2026-02-10",
      "time": "10:00",
      "interviewer_name": "Raj Patel",
      "interviewer_email": "raj@company.com",
      "meeting_link": "https://meet.google.com/xyz",
      "max_capacity": 4
    },
    {
      "date": "2026-02-10",
      "time": "14:00",
      "location": "Conference Room A",
      "max_capacity": 2
    }
  ]
}

Response:
{
  "message": "2 interview slots created",
  "slots": [...]
}
```

### B. View Slot Bookings

**API Endpoint:**
```
GET /api/company/interview-slot/{slot_id}/bookings

Response:
{
  "slot": {
    "id": 10,
    "slot_date": "2026-02-10",
    "slot_time": "10:00",
    "interviewer_name": "Raj Patel",
    "meeting_link": "https://meet.google.com/xyz",
    "max_capacity": 4,
    "current_bookings": 3,
    "status": "Available"
  },
  "bookings": [
    {
      "id": 1,
      "student_id": 456,
      "status": "Confirmed",
      "booked_at": "2026-01-20T15:30:00"
    }
  ],
  "available_spots": 1
}
```

**New Tables:**
```sql
CREATE TABLE interview_slots (
  id INT PRIMARY KEY,
  hiring_round_id INT FOREIGN KEY,
  company_id INT FOREIGN KEY,
  slot_date DATE,
  slot_time TIME,
  interviewer_name VARCHAR(255),
  interviewer_email VARCHAR(255),
  meeting_link VARCHAR(500),
  location VARCHAR(255),
  max_capacity INT DEFAULT 1,
  current_bookings INT DEFAULT 0,
  status ENUM('Available', 'Full', 'Completed', 'Cancelled'),
  created_at TIMESTAMP
);

CREATE TABLE interview_bookings (
  id INT PRIMARY KEY,
  interview_slot_id INT FOREIGN KEY,
  application_round_id INT FOREIGN KEY,
  student_id INT FOREIGN KEY,
  status ENUM('Confirmed', 'No-Show', 'Rescheduled', 'Completed'),
  booking_notes TEXT,
  booked_at TIMESTAMP
);
```

---

## 4. DIGITAL OFFER LETTER GENERATION

### A. Generate Offer Letter

**Features:**
- Pre-filled with job and candidate details
- Customizable offer terms
- Auto-generates professional HTML letter
- 7-day expiry by default

**API Endpoint:**
```
POST /api/company/application/{application_id}/generate-offer
{
  "designation": "Senior Software Engineer",
  "ctc": "20 LPA",
  "annual_ctc": 2000000,
  "job_location": "Bangalore",
  "joining_date": "2026-03-15",
  "notice_period": 30
}

Response:
{
  "message": "Offer letter generated",
  "offer_id": 99,
  "offer": {
    "id": 99,
    "designation": "Senior Software Engineer",
    "ctc": "20 LPA",
    "annual_ctc": 2000000,
    "job_location": "Bangalore",
    "joining_date": "2026-03-15",
    "status": "Generated",
    "created_at": "2026-01-20T10:00:00"
  }
}
```

### B. Send Offer Letter to Student

**API Endpoint:**
```
POST /api/company/offer/{offer_id}/send

Response:
{
  "message": "Offer letter sent to student",
  "offer_id": 99,
  "sent_date": "2026-01-20T10:05:00"
}
```

**Generated Offer Letter (HTML Template):**
```html
<html>
  <h2>TechCorp</h2>
  <h3>Official Offer Letter</h3>
  
  <p>Dear Rajesh Kumar,</p>
  <p>We are pleased to offer you the position of Senior Software Engineer...</p>
  
  <table>
    <tr><td>Position:</td><td>Senior Software Engineer</td></tr>
    <tr><td>Location:</td><td>Bangalore</td></tr>
    <tr><td>CTC:</td><td>20 LPA</td></tr>
    <tr><td>Joining Date:</td><td>15-Mar-2026</td></tr>
  </table>
  
  <p>Please confirm within 7 days...</p>
</html>
```

**New Table:**
```sql
CREATE TABLE offer_letters (
  id INT PRIMARY KEY,
  application_id INT FOREIGN KEY,
  company_id INT FOREIGN KEY,
  student_id INT FOREIGN KEY,
  designation VARCHAR(255),
  ctc VARCHAR(100),
  annual_ctc DECIMAL(12,2),
  job_location VARCHAR(255),
  joining_date DATE,
  notice_period INT,
  offer_content LONGTEXT,
  template_used VARCHAR(255),
  status ENUM('Generated', 'Sent', 'Accepted', 'Rejected', 'Expired'),
  sent_date TIMESTAMP,
  acceptance_date TIMESTAMP,
  expiry_date TIMESTAMP,
  created_at TIMESTAMP
);
```

---

## 5. HIRING ROUND PROGRESS TRACKING

### A. Get Hiring Rounds for Job

**API Endpoint:**
```
GET /api/company/job/{job_id}/hiring-rounds

Response:
[
  {
    "id": 1,
    "job_id": 5,
    "round_number": 1,
    "round_type": "Aptitude Test",
    "description": "General aptitude assessment",
    "duration_minutes": 60,
    "created_at": "2026-01-15T09:00:00"
  },
  ...
]
```

### B. Update Student's Round Progress

**API Endpoint:**
```
POST /api/company/hiring-round/{application_round_id}/update-progress
{
  "status": "Completed",
  "score": 85.5,
  "feedback": "Excellent technical knowledge",
  "mark_completed": true
}

Response:
{
  "message": "Progress updated",
  "application_round": {
    "id": 123,
    "status": "Completed",
    "score": 85.5,
    "feedback": "Excellent technical knowledge",
    "completed_at": "2026-01-20T14:30:00"
  }
}
```

---

## Frontend Usage

### Access the Dashboard
```
http://localhost:3000/company-advanced.html
```

### Login Credentials
```
Email: company@techcorp.com
Password: password123
```

### Tabs Overview

1. **Overview Tab**
   - View all job postings
   - Statistics (total jobs, active jobs, total applications)

2. **Create Drive Tab**
   - Multi-step wizard for creating jobs
   - Step-by-step guide through eligibility and hiring process

3. **Applicants Tab**
   - Advanced filtering and sorting
   - Bulk resume download
   - Status management
   - Generate offer letters

4. **Interview Scheduling Tab**
   - View hiring rounds
   - Create interview slots
   - Calendar interface
   - Manage bookings

5. **Offer Letters Tab**
   - View all generated offers
   - Track sent/accepted status
   - Monitor expiry dates

---

## Database Schema Summary

### New Tables
1. **hiring_rounds** - Defines rounds in hiring process
2. **application_rounds** - Tracks student progress per round
3. **interview_slots** - Available interview time slots
4. **interview_bookings** - Student bookings for interview slots
5. **offer_letters** - Digital offer letter records

### Modified Tables
- **jobs** - Added: min_10th_percentage, min_12th_percentage
- Jobs now support JSON-based eligible_branches array

### Complete Relationship Diagram
```
User
├── Student
│   └── Applications
│       ├── Application
│       │   ├── ApplicationRounds
│       │   │   └── InterviewBookings
│       │   └── OfferLetters
│       └── InterviewBookings
└── Company
    └── Jobs
        ├── HiringRounds
        │   ├── InterviewSlots
        │   │   └── InterviewBookings
        │   └── ApplicationRounds
        └── OfferLetters
```

---

## Best Practices

1. **Eligibility Criteria**
   - Store branches as JSON array: `["CSE", "IT"]`
   - Always validate candidate CGPA and branch before offering

2. **Interview Scheduling**
   - Define capacity per slot based on interviewer availability
   - Consider timezone if hiring remotely

3. **Offer Letters**
   - Set reasonable expiry periods (5-7 days standard)
   - Include clear joining date and notice period
   - Track acceptance status

4. **Bulk Operations**
   - Validate CSV format before upload
   - Provide error reports for failed rows
   - Allow partial updates (don't fail on single errors)

---

## Testing Checklist

- [ ] Create Drive Wizard completes all 3 steps
- [ ] Eligible branches filter works correctly
- [ ] Smart filter hides ineligible candidates
- [ ] Bulk resume download creates ZIP file
- [ ] CSV bulk upload updates statuses
- [ ] Interview slots can be created and booked
- [ ] Offer letters generate with correct HTML
- [ ] Offer letters send to students
- [ ] Application status tracking works end-to-end

---

## Support

For issues or questions, refer to:
- Backend Routes: `/backend/company_advanced_routes.py`
- Database Models: `/backend/models.py`
- Frontend: `/frontend/company-advanced.html`
