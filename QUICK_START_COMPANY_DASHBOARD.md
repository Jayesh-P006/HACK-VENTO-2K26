# Quick Start Guide - Company Dashboard

## Access Instructions

### 1. Open Dashboard
```
URL: http://localhost:3000/company-advanced.html
```

### 2. Login
```
Email: company@techcorp.com
Password: password123
```

---

## Feature Quick Links

### Create Your First Job (Drive)
1. Click **Create Drive** tab
2. **Step 1**: Enter job details
   - Title: "Senior Software Engineer"
   - Type: "Full-Time"
   - Location: "Bangalore"
   - CTC: "18-25 LPA"
   - Description & requirements
   - Application deadline: Set date
3. **Step 2**: Set eligibility
   - Min CGPA: 8.0
   - Min 10th%: 70
   - Min 12th%: 75
   - Select branches: CSE, IT
4. **Step 3**: Configure rounds
   - Add rounds: Aptitude → GD → Tech → HR
   - Set duration for each
5. Click **Publish**

**Result**: Job is live and accepting applications!

---

### Find & Filter Applicants
1. Click **Applicants** tab
2. Select job from dropdown
3. Use filters:
   - **Min CGPA**: Enter 8.0
   - **Branch**: Select CSE
   - **Status**: Select Shortlisted
   - **Hide Ineligible**: Check to remove unqualified candidates
4. Results update in real-time

---

### Bulk Operations

#### Download All Resumes
1. Select applicants with checkboxes
2. Click **Download Resumes**
3. Receives ZIP file with all PDFs

#### Bulk Update Status
1. Click **Bulk Upload Status**
2. Upload CSV with format:
   ```
   student_id,status
   456,Shortlisted
   789,Interview
   ```
3. System updates all records

---

### Schedule Interviews
1. Go to **Interview Scheduling** tab
2. Select a job
3. Click on a hiring round
4. Create interview slots:
   - Date: 2026-02-10
   - Time: 10:00 AM
   - Interviewer: Name & email
   - Type: Online (meeting link) or Onsite (location)
   - Capacity: How many candidates per slot
5. Slots are now ready for student bookings

---

### Send Offer Letters
1. Find applicant in **Applicants** tab
2. Click **Offer** button
3. Fill offer details:
   - Designation: "Senior Software Engineer"
   - CTC: "20 LPA"
   - Location: "Bangalore"
   - Joining Date: "2026-03-15"
4. Click **Generate & Send**
5. Offer letter generated and sent!

---

## API Endpoints (For Developers)

### Base URL
```
http://localhost:5000/api
```

### Authentication Header
```
Authorization: Bearer {JWT_TOKEN}
```

### Key Endpoints

#### Create Job (Step 1)
```
POST /company/create-drive/step1
Body: {
  "title": "...",
  "job_type": "Full-Time",
  "location": "...",
  "ctc": "...",
  "description": "...",
  "application_deadline": "2026-03-31"
}
```

#### Get Applicants with Smart Filter
```
GET /company/job/{job_id}/applicants/advanced?hide_ineligible=true&min_cgpa=8.0
```

#### Upload Bulk Status
```
POST /company/job/{job_id}/bulk-status-upload
(Form data with CSV file)
```

#### Create Interview Slots
```
POST /company/job/{job_id}/interview-slots
Body: {
  "hiring_round_id": 1,
  "slots": [
    {
      "date": "2026-02-10",
      "time": "10:00",
      "interviewer_name": "John",
      "meeting_link": "https://...",
      "max_capacity": 4
    }
  ]
}
```

#### Generate Offer Letter
```
POST /company/application/{application_id}/generate-offer
Body: {
  "designation": "Senior Software Engineer",
  "ctc": "20 LPA",
  "job_location": "Bangalore",
  "joining_date": "2026-03-15"
}
```

---

## Demo Accounts

### Company (Recruiter)
```
Email: company@techcorp.com
Password: password123
```

### Student (For Testing Applications)
```
Email: student@university.edu
Password: password123
```

### Admin (For Approving Jobs)
```
Email: admin@university.edu
Password: password123
```

---

## Keyboard Shortcuts

- **Tab**: Move between form fields
- **Enter**: Submit form
- **Escape**: Close modals
- **Ctrl+A**: Select all checkboxes

---

## Troubleshooting

### Job Not Appearing
- Check if job status is "Approved" (admin verification needed)
- Verify application deadline is in future

### Applicants Not Showing
- Ensure job is selected
- Check if applicants have actually applied
- Use "Hide Ineligible" to filter out unqualified

### Interview Slots Not Visible
- Create hiring rounds first (Step 3 of wizard)
- Ensure job is published
- Check that hiring_round_id is valid

### Offer Not Sending
- Verify student has a valid email
- Check database connection
- Review error message for details

---

## Best Practices

1. **Create Drives**: Use 3-step wizard for consistent setup
2. **Filter Smart**: Use "Hide Ineligible" to focus on qualified candidates
3. **Bulk Operations**: Always verify CSV format before upload
4. **Interview Scheduling**: Set realistic time slots and capacity
5. **Offer Letters**: Customize terms per candidate if needed
6. **Tracking**: Regularly update application status and round progress

---

## Support

### Documentation Files
- `COMPANY_DASHBOARD_GUIDE.md` - Full API documentation
- `COMPANY_DASHBOARD_IMPLEMENTATION.md` - Technical details
- `README.md` - General project info

### Backend Code
- `backend/company_advanced_routes.py` - All API logic
- `backend/models.py` - Database models
- `backend/app.py` - Main Flask app

### Frontend Code
- `frontend/company-advanced.html` - Dashboard UI

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Next field |
| Shift+Tab | Previous field |
| Enter | Submit |
| Esc | Close modal |
| Space | Toggle checkbox |

---

**Last Updated**: January 1, 2026  
**Version**: 1.0  
**Status**: Production Ready
