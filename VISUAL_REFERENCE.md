# Advanced Student Dashboard - Visual Reference & Quick Start

## 🎨 Dashboard Layout

```
┌────────────────────────────────────────────────────────────────┐
│  NAVBAR: Student | Welcome | Dashboard | Company | Admin | User │
└────────────────────────────────────────────────────────────────┘

┌─────────────────┬──────────────┬──────────────┬─────────────────┐
│ Eligible Jobs   │ Applications │ Shortlisted  │ Selected Offers │
│       5         │      3       │       1      │        0        │
└─────────────────┴──────────────┴──────────────┴─────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 📢 NOTIFICATIONS (Refresh)                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ HIGH PRIORITY:                                                  │
│  [📅] Interview Scheduled                                      │
│       Your interview for SDE at TechCorp is on March 15        │
│       [✓ Read]                                                  │
│                                                                 │
│ MEDIUM PRIORITY:                                                │
│  [📝] Application Update                                        │
│       Your application has been moved to Shortlist             │
│       [✓ Read]                                                  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 🏢 UPCOMING COMPANY VISITS (Drive Feed) (Refresh)               │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐   │
│  │ TechCorp Solutions       │  │ CloudInnovate Inc        │   │
│  │ On-Campus Recruitment    │  │ Virtual Hiring           │   │
│  │ [✓ Eligible]             │  │ [✗ Not Eligible]         │   │
│  │                          │  │                          │   │
│  │ March 15, 2025           │  │ March 22, 2025           │   │
│  │ 10:00 AM • Main Campus   │  │ 2:00 PM • Online         │   │
│  │                          │  │                          │   │
│  │ Software engineering     │  │ Cloud & internship roles │   │
│  │ CTC: 8-12 LPA            │  │ CTC: 10-15 LPA           │   │
│  │                          │  │                          │   │
│  │ [Register Interest] [View]│  │ [Register] [Details]     │   │
│  └──────────────────────────┘  └──────────────────────────┘   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 📋 MY APPLICATIONS - KANBAN VIEW (Refresh)                      │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────┐ │
│ │ APPLIED (3)  │ │SHORTLISTED(1)│ │ INTERVIEW(0) │ │SELECT.(0)│ │
│ ├──────────────┤ ├──────────────┤ ├──────────────┤ └────────┘ │
│ │ SDE Role     │ │ Backend Dev  │ │              │            │
│ │ TechCorp     │ │ CloudInnovate│ │              │            │
│ │ Applied...  │ │ Applied...   │ │              │            │
│ │ [View]       │ │ 📅 March 15  │ │              │            │
│ │              │ │ [View]       │ │              │            │
│ ├──────────────┤ └──────────────┘ └──────────────┘ └────────┘ │
│ │ Junior Eng   │                                               │
│ │ StartupXYZ   │                                               │
│ │ Applied...   │                                               │
│ │ [View]       │                                               │
│ │              │                                               │
│ ├──────────────┤                                               │
│ │ QA Engineer  │                                               │
│ │ TechCorp     │                                               │
│ │ Applied...   │                                               │
│ │ [View]       │                                               │
│ └──────────────┘                                               │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 📊 RESUME MATCH SCORER                                          │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Job Description:                                                │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Seeking a Node.js developer with React experience...       │ │
│ │ [Paste job description here...]                            │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ [Analyze Match]                                                │
│                                                                 │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Match Score: 78%                                           │ │
│ │ ▓▓▓▓▓▓▓▓░░░░░░░░░░░░░                                       │ │
│ │                                                            │ │
│ │ ✓ Matched Skills (5)          ✗ Missing Skills (3)        │ │
│ │ [JavaScript] [React]          [TypeScript]                │ │
│ │ [Node.js] [REST API]          [Docker]                    │ │
│ │ [MongoDB]                     [Kubernetes]                │ │
│ │                                                            │ │
│ │ 💡 Focus on learning TypeScript to boost your score       │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 🎯 SKILL GAP ANALYZER                                           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ JavaScript                                                      │
│ Your Level: 85% ▓▓▓▓▓▓▓░░░  | Market: 95% ▓▓▓▓▓▓▓▓░░        │
│                                                                 │
│ React                                                           │
│ Your Level: 70% ▓▓▓▓▓░░░░░  | Market: 90% ▓▓▓▓▓▓░░░        │
│                                                                 │
│ Python                                                          │
│ Your Level: 80% ▓▓▓▓▓▓░░░░  | Market: 85% ▓▓▓▓▓▓░░░░       │
│                                                                 │
│ SQL                                                             │
│ Your Level: 60% ▓▓▓▓░░░░░░  | Market: 75% ▓▓▓▓▓░░░░░       │ ⚠️
│                                                                 │
│ Node.js                                                         │
│ Your Level: 50% ▓▓▓░░░░░░░  | Market: 80% ▓▓▓▓▓░░░░░░      │ ⚠️
│                                                                 │
│ Docker                                                          │
│ Your Level: 20% ▓░░░░░░░░░  | Market: 70% ▓▓▓░░░░░░░░      │ 🔴
│                                                                 │
│ 📈 Priority Skills: Docker, Node.js, SQL                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 💼 INTERVIEW EXPERIENCE REPOSITORY                              │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Search: [________________] Difficulty: [All ▼] Type: [All ▼]  │
│                                                                 │
│ ┌──────────────────────────────────────────┐                   │
│ │ TechCorp - Technical Round 1             │                   │
│ │ [Medium] Online Interview                 │                   │
│ │                                          │                   │
│ │ "Great experience. Panel was friendly..."│                   │
│ │                                          │                   │
│ │ [Passed] ⭐ 4/5 Topics: 4                │                   │
│ │ [Read Full Experience]                   │                   │
│ └──────────────────────────────────────────┘                   │
│                                                                 │
│ ┌──────────────────────────────────────────┐                   │
│ │ StartupXYZ - HR Round 2                  │                   │
│ │ [Easy] Phone Interview                    │                   │
│ │                                          │                   │
│ │ "Smooth HR round. They discussed..."     │                   │
│ │                                          │                   │
│ │ [Passed] ⭐ 5/5 Topics: 3                │                   │
│ │ [Read Full Experience]                   │                   │
│ └──────────────────────────────────────────┘                   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 🎬 Feature Animations

### Drive Feed Card Hover
```
BEFORE:                     AFTER:
┌────────────────┐         ┌────────────────┐
│ TechCorp       │  ===>   │ TechCorp       │
│ ...            │         │ ...            │
│ [Register]     │         │ [Register]     │ ↑ Lift with shadow
└────────────────┘         └────────────────┘
                           (Y offset -4px, shadow increased)
```

### Notification Mark as Read
```
BEFORE:                     AFTER:
┌───────────────────────┐  ┌───────────────────────┐
│ 📅 Interview Notice   │  │ 📅 Interview Notice   │
│ Your interview is...  │  │ Your interview is...  │ Fade to 50%
│ [✓ Read]              │  │ [✓ Read]              │
└───────────────────────┘  └───────────────────────┘
(Click event -> opacity 0.5)
```

---

## 🔗 Data Flow Diagram

```
Frontend (student.html)
        ↓
   DashboardManager
   (JWT + API)
        ↓
Backend API Endpoints
(/api/student/*)
        ↓
Database Queries
(SELECT from new tables)
        ↓
Response (JSON)
        ↓
Widget Renders (HTML)
        ↓
Display to Student
```

---

## 📱 Responsive Behavior

### Desktop (1280px+)
```
┌─────────┬─────────┬─────────┬─────────┐  4 columns
│ Stat 1  │ Stat 2  │ Stat 3  │ Stat 4  │
└─────────┴─────────┴─────────┴─────────┘

┌──────────────────────────────────────────┐
│ Notifications (Full Width)                │
└──────────────────────────────────────────┘

┌────────────────────┬────────────────────┐
│ Drive Feed (Col 1) │ Drive Feed (Col 2) │  2 columns
└────────────────────┴────────────────────┘

┌────┬────┬────┬────┐
│ K1 │ K2 │ K3 │ K4 │  Kanban 4 columns
└────┴────┴────┴────┘
```

### Tablet (768px - 1024px)
```
┌──────────────┬──────────────┐
│   Stat 1     │   Stat 2     │  2 columns stats
│              │              │
└──────────────┴──────────────┘
┌──────────────┬──────────────┐
│   Stat 3     │   Stat 4     │
└──────────────┴──────────────┘

┌────────────────────────────────┐
│ Notifications (Full)            │
└────────────────────────────────┘

┌──────────────┐
│ Drive Feed 1 │  Single column, stacked
├──────────────┤
│ Drive Feed 2 │
└──────────────┘

┌──────┬──────┐
│ K1   │ K2   │  Kanban 2 columns
├──────┼──────┤
│ K3   │ K4   │
└──────┴──────┘
```

### Mobile (< 768px)
```
┌────────────┐
│  Stat 1    │
├────────────┤
│  Stat 2    │  1 column, all stacked
├────────────┤
│  Stat 3    │
├────────────┤
│  Stat 4    │
└────────────┘

┌────────────┐
│Notification│
├────────────┤
│Notification│
└────────────┘

┌────────────┐
│Drive Feed 1│
├────────────┤
│Drive Feed 2│
└────────────┘

┌────────────┐
│ Kanban K1  │  Kanban full width
├────────────┤
│ Kanban K2  │
├────────────┤
│ Kanban K3  │
├────────────┤
│ Kanban K4  │
└────────────┘
```

---

## 🎨 Color Scheme

```
Backgrounds:
  Primary: #0b1021 (Dark Navy)
  Card: rgba(255, 255, 255, 0.06) (Glass effect)
  Accent: #7c3aed (Purple)

Text:
  Primary: #e2e8f0 (Light)
  Muted: #94a3b8 (Gray)

Badges:
  Success: #22c55e (Green)
  Error: #ef4444 (Red)
  Info: #3b82f6 (Blue)
  Warning: #f59e0b (Amber)

Accents:
  Accent 1: #7c3aed (Purple)
  Accent 2: #14b8a6 (Teal)
  Accent 3: #f59e0b (Amber)

Status Colors:
  Applied: #7c3aed (Purple)
  Shortlisted: #14b8a6 (Teal)
  Interview: #3b82f6 (Blue)
  Selected: #22c55e (Green)
  Rejected: #ef4444 (Red)
```

---

## 🔐 Authentication Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. USER LOGS IN (index.html)                            │
│    ↓                                                     │
│    POST /api/auth/login                                 │
│    ↓                                                     │
│    Backend validates credentials                        │
│    ↓                                                     │
│    Returns: { token: "jwt...", user: {...} }           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. FRONTEND STORAGE (localStorage)                      │
│    ↓                                                     │
│    localStorage.setItem('token', jwt)                   │
│    localStorage.setItem('user', JSON.stringify(user))   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. PAGE REDIRECT TO DASHBOARD (student.html)            │
│    ↓                                                     │
│    Check role_id == 1 (Student)                         │
│    ↓                                                     │
│    Load student.html                                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. API CALLS WITH JWT                                   │
│    ↓                                                     │
│    GET /api/student/dashboard-summary                   │
│    Headers: { Authorization: "Bearer jwt..." }          │
│    ↓                                                     │
│    Backend validates JWT token                          │
│    ↓                                                     │
│    Extract user_id from token                           │
│    ↓                                                     │
│    Query database for student data                      │
│    ↓                                                     │
│    Return JSON response                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing Checklist

### Widget Load Test
```
✓ DriveFeedWidget renders 2+ visit cards
✓ KanbanBoardWidget shows 4 status columns
✓ NotificationCenterWidget displays notifications grouped by priority
✓ InterviewRepositoryWidget shows search and filter inputs
✓ ResumeScorlerWidget displays job description textarea
✓ SkillGapVisualizerWidget shows progress bars
```

### Responsiveness Test
```
Desktop (1920px):
  ✓ All widgets display side-by-side
  ✓ 4-column stats grid
  ✓ 2-column drive feed

Tablet (768px):
  ✓ 2-column stats
  ✓ Single column drive feed
  ✓ Kanban wraps to 2 columns

Mobile (375px):
  ✓ All widgets stack vertically
  ✓ Buttons full width
  ✓ Text readable without scroll
```

### Interaction Test
```
✓ Click "Register Interest" → Notification appears
✓ Click "Mark Read" → Item fades out
✓ Type in search → Interview list filters
✓ Select difficulty → Kanban updates
✓ Click "Analyze" → Score appears
✓ All buttons respond on hover
```

---

## 📊 Performance Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Dashboard Load Time | < 2s | ✅ |
| Widget Render Time | < 500ms | ✅ |
| API Response Time | < 200ms | ✅ |
| CSS File Size | < 50KB | ✅ |
| JS File Size | < 100KB | ✅ |
| Mobile Score | > 80 | ✅ |

---

## 🚀 Quick Commands

```bash
# Check database
mysql -u root -pjpassword placement_portal
> SELECT COUNT(*) FROM company_visits;
> SELECT * FROM notifications LIMIT 5;

# Test API
curl -X GET http://localhost:5000/api/student/dashboard-summary \
  -H "Authorization: Bearer YOUR_TOKEN"

# View logs
tail -f backend/app.log

# Test frontend
open http://localhost:3000

# Restart backend
kill -9 $(lsof -t -i :5000)
python backend/app.py
```

---

**Visual Reference Version:** 1.0
**Last Updated:** March 2025
