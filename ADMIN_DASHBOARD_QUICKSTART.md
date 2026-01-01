# Admin (TPO) Dashboard - Quick Start Guide

## 🎓 Overview

The Admin Control Center is a comprehensive dashboard for Placement & Internship Portal administrators (TPOs). It provides complete management of student verification, disciplinary actions, master data, and placement analytics.

---

## 📊 What's New?

### Database Schema (7 New Tables)
1. **student_verification** - Document approval queue
2. **student_blacklist** - Disciplinary freeze list
3. **departments** - Department master data
4. **batch_years** - Batch/graduation years
5. **skills** - Technical skills master list
6. **placement_stats** - Placement analytics
7. **company_visits** - Company recruitment tracking

### API Endpoints (22 New Routes)
- 3 Verification Queue endpoints
- 3 Blacklist Management endpoints
- 10 Master Data endpoints (CRUD)
- 5 Analytics endpoints
- 2 Reports/Export endpoints

### UI Components
- 6 Main Tabs with 10+ subtabs
- Interactive Chart.js visualizations
- Server-side paginated tables (2000+ records)
- Real-time conflict detection
- Master data CRUD forms
- Export to CSV

---

## 🚀 Getting Started

### 1. **Access the Dashboard**

URL: `http://localhost:3000/admin-dashboard.html`

Login with Admin credentials:
```
Email: admin@tpo.edu (or any admin user)
Password: <your_password>
Role: Admin (3)
```

### 2. **Create Admin User (if needed)**

```python
from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create admin user
    admin = User(
        email='admin@tpo.edu',
        password_hash=generate_password_hash('password123'),
        role_id=3,  # Admin role
        is_verified=True
    )
    db.session.add(admin)
    db.session.commit()
    print(f"Admin user created: ID {admin.id}")
```

---

## 📋 Feature Walkthrough

### **Tab 1: Overview Dashboard**

**What you see:**
- 📊 Statistics cards (Total Students, Placed, Unplaced, Placement Rate)
- 💰 Package info (Highest, Average)
- 📍 Active company visits table
- 🚨 Scheduling conflict alerts
- 📈 Pie charts and bar graphs

**Key Actions:**
- Click "Check for Conflicts" to detect overlapping company visits
- Monitor real-time placement statistics
- View active recruitment drives

**Sample Data:**
```
Total Students: 200
Placed: 120
Unplaced: 80
Placement Rate: 60%
Highest Package: ₹24.50 LPA
Average Package: ₹14.75 LPA
```

---

### **Tab 2: Verification Queue**

**What you see:**
- Table of students awaiting document verification
- Status filter (All, Pending, Verified, Rejected)
- Server-side pagination

**How to verify students:**

1. **Approve Document**
   - Click "Approve" button
   - Student's account is automatically activated
   - They can now apply for drives

2. **Reject Document**
   - Click "Reject" button
   - Enter rejection reason (e.g., "Blurry mark sheets")
   - Student notified and asked to resubmit

**API Calls Made:**
```
GET /api/admin/verification-queue?status=Pending&page=1
POST /api/admin/verification/{id}/approve
POST /api/admin/verification/{id}/reject
```

---

### **Tab 3: Blacklist Management**

**What you see:**
- List of blacklisted students
- Severity levels (Low, Medium, High, Critical)
- Blacklist duration/expiry

**How to blacklist a student:**

1. Click **"+ Add to Blacklist"** button
2. Fill the form:
   ```
   Student ID: 5
   Reason: "No-show in Infosys interview"
   Severity: High
   Duration (days): 60 (leave blank for permanent)
   ```
3. Submit

**Effects of Blacklisting:**
- ✓ Prevents applications to new drives
- ✓ Removes from candidate lists
- ✓ Auto-unlocks after duration expires
- ✓ Permanent if no duration set

**API Calls Made:**
```
GET /api/admin/blacklist/students
POST /api/admin/blacklist/add
POST /api/admin/blacklist/remove/{id}
```

---

### **Tab 4: Master Data Management**

#### **4a. Departments**

Create/manage academic departments:
```
Code: CSE
Name: Computer Science & Engineering
Description: Core CS department
```

Pre-seeded with:
- CSE, IT, ECE, EEE, MECH, CIVIL

#### **4b. Batch Years**

Manage graduation batches:
```
Year: 2024
Academic Session: 2024-2025
```

Pre-seeded with:
- 2023, 2024, 2025

#### **4c. Skills**

Maintain skill taxonomy:
```
Name: React
Category: Framework
Description: React JS library
```

Pre-seeded with 8 skills:
- Python, Java, JavaScript, React, SQL, MongoDB, AWS, Docker

**How to Add:**
1. Click "+ Add [Master]" button
2. Fill form
3. Submit

**API Calls:**
```
GET /api/admin/departments
POST /api/admin/departments
PUT /api/admin/departments/{id}

GET /api/admin/batch-years
POST /api/admin/batch-years

GET /api/admin/skills
POST /api/admin/skills
```

---

### **Tab 5: Analytics**

**Real-time Dashboards:**

1. **Placement Trend Chart**
   - Shows placement progression over time
   - Uses line chart

2. **Package Distribution**
   - Shows CTC distribution
   - Uses histogram

3. **Department-wise Analytics Table**
   ```
   Department | Total Students | Placed | Unplaced | Rate
   CSE        | 80             | 50     | 30       | 62.5%
   IT         | 60             | 35     | 25       | 58.3%
   ```

**API Calls:**
```
GET /api/admin/analytics/placement-stats
GET /api/admin/analytics/company-visits
GET /api/admin/analytics/department-stats
```

---

### **Tab 6: Reports**

**Three Export Options:**

1. **Export Student Data**
   - Downloads CSV with all student records
   - Columns: Enrollment #, Name, Email, Branch, CGPA, Year, Placement Status, Profile Status

2. **Generate Placement Report**
   - Creates summary report in dashboard
   - Shows all key metrics
   - Date-stamped

3. **Download Excel**
   - Alias for export student data
   - Opens in Excel/Sheets

**API Calls:**
```
GET /api/admin/reports/student-data
GET /api/admin/reports/placement-report
```

---

## 🎯 Common Use Cases

### **Use Case 1: Verify New Students**

1. Go to **Verification Queue** tab
2. See "Pending" students with their enrollment details
3. Click "Approve" for valid documents
4. Student account is activated
5. They can now apply for drives

### **Use Case 2: Discipline a Student (No-show)**

1. Go to **Blacklist** tab
2. Click "+ Add to Blacklist"
3. Enter Student ID and reason
4. Set duration (e.g., 60 days)
5. Student's account is frozen for that period

### **Use Case 3: Check Placement Status**

1. Go to **Overview** tab
2. View statistics cards
3. Check pie chart for Placed vs Unplaced ratio
4. Review department-wise breakdown
5. Export report if needed

### **Use Case 4: Detect Company Visit Conflicts**

1. Go to **Overview** tab
2. Click "Check for Conflicts"
3. See alert if two companies scheduled on same date
4. Adjust schedule or notify companies

### **Use Case 5: Add New Department**

1. Go to **Master Data** → **Departments**
2. Click "+ Add Department"
3. Enter: Code (e.g., "BIO"), Name, Description
4. Submit
5. Department added to master list

---

## 📊 Analytics Metrics

### Key Performance Indicators (KPIs)

**Placement Metrics:**
- Total Students
- Placed Count
- Unplaced Count
- Placement Rate (%)
- Highest Package (LPA)
- Average Package (LPA)

**Company Metrics:**
- Total Companies Visiting
- Companies in Interview Stage
- Total Applications Received
- Shortlisted Candidates
- Selected Candidates

**Department Metrics:**
- Total Students per Department
- Placed per Department
- Placement Rate per Department (%)

---

## 🔧 Technical Details

### Database Query Performance

**Pagination for 2000+ Records:**
```python
# Server-side pagination (default 20 per page)
GET /api/admin/verification-queue?page=1&per_page=20
```

**Placement Stats Calculation:**
```python
# Cached daily or on-demand
placed = COUNT(DISTINCT offers.student_id WHERE status IN ('Sent', 'Accepted'))
avg_package = AVERAGE(annual_ctc) FROM offer_letters
dept_breakdown = GROUP BY branch
```

**Conflict Detection:**
```python
# Check visits within 2-hour window on same date
if date_match and time_diff < 2 hours:
    conflict detected
```

---

## 📁 Files Created

```
backend/
├── admin_routes.py          (450+ lines, 22 endpoints)
├── models.py                (Enhanced with 7 new models)
└── app.py                   (Updated with blueprint)

frontend/
├── admin-dashboard.html     (1200+ lines, Chart.js integration)

Documentation/
├── ADMIN_DASHBOARD_API.md   (Complete API reference)
└── ADMIN_DASHBOARD_QUICKSTART.md (This file)
```

---

## 🔐 Security Features

✓ JWT Authentication (Admin role only)  
✓ Role-based access control (role_id = 3)  
✓ CSRF protection via session tokens  
✓ Database constraints (unique, foreign keys)  
✓ Transaction rollback on errors  
✓ Server-side validation  

---

## 🚨 Important Notes

### Student Verification
- Students cannot apply for drives until **Verified**
- Mark sheets visibility set by student during registration
- Admins must approve within reasonable timeframe

### Blacklisting
- **Temporary:** Auto-removes on expiry date
- **Permanent:** Must manually remove from blacklist
- Blacklisted students' profiles show as inactive

### Master Data
- **Departments:** Cannot delete if students assigned
- **Skills:** Can be marked inactive instead of deleting
- **Batch Years:** Required for student registration

### Analytics
- Stats calculated on-demand (small performance overhead)
- Cached for 1 hour in production
- Conflict detection runs in real-time

---

## 🐛 Troubleshooting

### "Unauthorized" Error
**Solution:** Ensure you're logged in as Admin (role_id = 3)

### Missing Tables
**Solution:** Run database initialization:
```python
from app import app
from models import db
with app.app_context():
    db.create_all()
```

### Pagination Not Working
**Solution:** Check `per_page` parameter (max 100)

### Charts Not Rendering
**Solution:** Check browser console for Chart.js errors, ensure data exists

---

## 📞 Support

For issues:
1. Check ADMIN_DASHBOARD_API.md for endpoint details
2. Verify JWT token is valid
3. Check database connection
4. Review browser console for JavaScript errors

---

## 🎉 Next Steps

1. **Test Verification:** Add a test student, verify documents
2. **Test Blacklist:** Blacklist a test student, verify freezing
3. **Add Masters:** Create new department, batch, skill
4. **Generate Reports:** Export student data, placement report
5. **Monitor Analytics:** Check placement progress daily

---

**Dashboard Ready! Happy Administering! 🎓**
