# Advanced Student Dashboard - Widget System Documentation

## Overview

The Student Dashboard has been upgraded with 6 modular, reusable widget components that provide comprehensive career management tools. Each widget is self-contained, manages its own state, and communicates through a centralized `DashboardManager`.

## Architecture

```
Frontend Structure:
├── assets/
│   ├── css/
│   │   └── styles.css (includes widget styles)
│   └── js/
│       ├── dashboard-widgets.js (all widget classes)
│       └── app.js (utility functions)
├── student.html (main dashboard page)
```

## Widget Classes

### 1. **DashboardManager**
Central coordinator for all dashboard operations.

**Features:**
- Unified API client with JWT authentication
- Toast notification system
- Widget registration and initialization
- Data caching (optional)

**Usage:**
```javascript
const manager = new DashboardManager(auth);
manager.api('/student/jobs').then(data => console.log(data));
manager.showToast('Success message', 'success');
```

---

### 2. **DriveFeedWidget** 
Live company visiting/recruitment schedule with skill eligibility matching.

**Features:**
- Display upcoming company visits with details
- Automatic skill matching against job requirements
- Eligibility badge (Green: Eligible, Red: Not Eligible)
- Register interest button
- Responsive card layout

**HTML Container:**
```html
<div id="drive-feed-widget"></div>
```

**Data Structure:**
```javascript
{
  id: 1,
  company_name: "TechCorp",
  recruitment_type: "On-Campus Recruitment",
  visit_date: "2025-03-15T10:00:00Z",
  visit_time: "10:00 AM",
  location: "Main Campus",
  description: "Annual recruitment drive",
  expected_ctc_range: "8-12 LPA",
  eligibility_criteria: "JavaScript, React, Node.js, 7+ CGPA"
}
```

**API Endpoints Used:**
- `GET /api/student/company-visits/upcoming` - Fetch upcoming visits
- `POST /api/student/company-visits/{visit_id}/register` - Register interest

---

### 3. **KanbanBoardWidget**
Application status tracking with visual column-based organization.

**Features:**
- Group applications by status (Applied, Shortlisted, Interview, Selected)
- Display count per status
- Drag-and-drop ready structure
- Quick view button for each application
- Interview date display (if scheduled)

**HTML Container:**
```html
<div id="kanban-widget"></div>
```

**Data Structure:**
```javascript
{
  id: 1,
  job_title: "Senior Developer",
  company_name: "TechCorp",
  status: "Shortlisted",
  applied_at: "2025-02-01T10:00:00Z",
  interview_date: "2025-03-15T14:00:00Z",
  interview_location: "Board Room A"
}
```

**API Endpoints Used:**
- `GET /api/student/applications` - Fetch all applications
- `PUT /api/student/applications/{app_id}` - Update status

---

### 4. **NotificationCenterWidget**
Real-time alerts and updates grouped by priority.

**Features:**
- Display notifications with type-specific icons
- Priority-based grouping (High, Medium, Low)
- Mark as read functionality
- Timestamp display
- Emoji indicators for notification types

**HTML Container:**
```html
<div id="notification-widget"></div>
```

**Notification Types:**
- 📅 `interview_schedule` - Interview scheduled
- 📝 `application_update` - Application status changed
- 🎯 `job_match` - Recommended job match
- 🏢 `company_visit` - Company visit announcement
- 📢 `announcement` - General announcement
- ⚡ `skill_alert` - Skill development alert

**API Endpoints Used:**
- `GET /api/student/notifications?unread=true` - Fetch unread notifications
- `PUT /api/student/notifications/{notif_id}/read` - Mark as read

---

### 5. **ResumeScorlerWidget**
Mock AI-powered resume analysis against job descriptions.

**Features:**
- Job description textarea input
- Resume match score (0-100%)
- Matched skills highlighting (green)
- Missing skills highlighting (red)
- Improvement recommendations
- Visual progress bar

**HTML Container:**
```html
<div id="resume-scorer-widget"></div>
```

**Score Calculation (Mock):**
- Extracts keywords from job description
- Compares against student's stored skills
- Calculates match percentage
- Lists missing and matched skills

**API Endpoints (Future):**
- `POST /api/student/resume-score` - Get AI score
- `GET /api/student/resume-score/{job_id}` - Get saved score

---

### 6. **SkillGapVisualizerWidget**
Visual comparison of student skills vs. market demand.

**Features:**
- Side-by-side progress bars for each skill
- Student proficiency level vs. market demand
- Priority skill recommendations
- Responsive grid layout

**HTML Container:**
```html
<div id="skill-gap-widget"></div>
```

**Data Structure:**
```javascript
{
  skill: "JavaScript",
  studentLevel: 85,        // 0-100
  marketDemand: 95         // 0-100
}
```

**Color Coding:**
- 🟢 Red: Gap > 30% (High priority)
- 🟡 Amber: Gap 15-30% (Medium priority)
- 🟢 Green: Gap < 15% (Low priority)

**API Endpoints Used:**
- `GET /api/student/skills` - Fetch skill assessments

---

### 7. **InterviewRepositoryWidget**
Searchable database of past interview experiences shared by community.

**Features:**
- Full-text search by company or topic
- Filter by difficulty level (Easy, Medium, Hard)
- Filter by interview type (Online, Phone, In-Person)
- Experience cards with rating display
- Outcome badges (Passed/Failed)
- Topic count indicator

**HTML Container:**
```html
<div id="interview-repo-widget"></div>
```

**Data Structure:**
```javascript
{
  id: 1,
  company_name: "TechCorp",
  interview_type: "Technical",
  interview_round: 1,
  difficulty_level: "Medium",
  duration_minutes: 60,
  topics_covered: "JavaScript, React, OOP",
  experience_summary: "Great experience...",
  questions_asked: [...],
  tips_advice: "...",
  outcome: "Passed",
  rating: 4,
  is_public: true,
  interview_date: "2025-02-15T10:00:00Z"
}
```

**API Endpoints Used:**
- `GET /api/interviews` - Fetch public experiences
- `GET /api/interviews?company={name}&difficulty={level}` - Advanced filtering
- `POST /api/student/interview-experience` - Share new experience

---

## Integration Guide

### Initialize Dashboard
```javascript
// Create manager instance
const manager = new DashboardManager(auth);

// Initialize widgets
const driveFeed = new DriveFeedWidget('#drive-feed-widget', manager);
const kanban = new KanbanBoardWidget('#kanban-widget', manager);
const notifications = new NotificationCenterWidget('#notification-widget', manager);

// Register widgets
manager.registerWidget('driveFeed', driveFeed);
manager.registerWidget('kanbanBoard', kanban);
manager.registerWidget('notificationCenter', notifications);

// Render with data
const visits = await manager.api('/student/company-visits/upcoming');
await driveFeed.render(visits);
```

### Widget Lifecycle
1. **Create**: `new WidgetClass(containerId, manager)`
2. **Register**: `manager.registerWidget(name, instance)`
3. **Render**: `widget.render(data)`
4. **Event Listeners**: Automatically attached during render
5. **Update**: Call `render()` again with fresh data

---

## CSS Classes & Styling

### Widget-Specific Classes
- `.kanban-board` - Main kanban container
- `.kanban-column` - Status columns
- `.kanban-card` - Individual application card
- `.notification-card` - Notification items
- `.interview-card` - Interview experience cards
- `.job-card` - Drive visit cards
- `.progress` - Progress bar element
- `.badge-*` - Badge variants (green, red, blue, amber)

### Responsive Breakpoints
```css
/* Desktop: All widgets on full width */
@media (min-width: 1024px) { ... }

/* Tablet: Kanban in 2 columns */
@media (max-width: 1024px) {
  .kanban-board { grid-template-columns: repeat(2, 1fr); }
}

/* Mobile: Single column layout */
@media (max-width: 768px) {
  .kanban-board { grid-template-columns: 1fr; }
}
```

---

## Backend API Reference

### Student Dashboard Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/student/dashboard-summary` | Summary stats |
| GET | `/api/student/jobs` | Eligible jobs |
| GET | `/api/student/applications` | All applications |
| GET | `/api/student/company-visits/upcoming` | Drive feed |
| POST | `/api/student/company-visits/{id}/register` | Register interest |
| GET | `/api/student/notifications` | All notifications |
| PUT | `/api/student/notifications/{id}/read` | Mark read |
| GET | `/api/student/skills` | Skill assessments |
| GET | `/api/interviews` | Interview experiences |
| POST | `/api/student/interview-experience` | Create experience |
| POST | `/api/student/resume-score` | Get AI score |

---

## Extending the Widgets

### Add New Property to Drive Feed
```javascript
// Modify createVisitCard() method
createVisitCard(visit) {
  // Add new field rendering
  return `
    ...
    <div class="new-field">${visit.new_property}</div>
    ...
  `;
}
```

### Custom Widget Creation
```javascript
class MyCustomWidget {
  constructor(containerId, manager) {
    this.container = document.querySelector(containerId);
    this.manager = manager;
  }

  async render(data) {
    this.container.innerHTML = this.createHTML(data);
    this.attachEventListeners();
  }

  createHTML(data) {
    return `<div>${data.map(item => `<div>${item.name}</div>`).join('')}</div>`;
  }

  attachEventListeners() {
    // Add event handlers
  }
}
```

---

## Testing the Widgets

### Manual Testing Checklist
- [ ] Drive Feed displays upcoming visits with eligibility badges
- [ ] Kanban board groups applications correctly
- [ ] Notification center marks items as read
- [ ] Resume scorer shows skill matches and gaps
- [ ] Skill gap visualizer displays correct percentages
- [ ] Interview repository filters work correctly
- [ ] All widgets are responsive on mobile/tablet
- [ ] Toast notifications appear for actions
- [ ] API calls use correct authentication header

### Mock Data Examples
All widgets come with pre-populated mock data for development:
```javascript
// In student.html loadDashboard()
const mockVisits = [{ id: 1, company_name: "TechCorp", ... }];
const mockNotifications = [{ id: 1, title: "Interview Scheduled", ... }];
const mockInterviews = [{ id: 1, company_name: "StartupXYZ", ... }];
```

---

## Performance Optimization

### Lazy Loading (Future Enhancement)
```javascript
// Load widgets only when visible
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting && !entry.target.loaded) {
      loadWidget(entry.target);
      entry.target.loaded = true;
    }
  });
});

observer.observe(document.querySelector('#interview-repo-widget'));
```

### Data Caching
```javascript
// Cache API responses to reduce network calls
manager.cache['jobs'] = jobsData;
if (manager.cache['jobs']) {
  driveFeed.render(manager.cache['jobs']);
}
```

---

## Error Handling

### Widget Error States
```javascript
async render(data) {
  if (!this.container) {
    console.warn('Container not found');
    return;
  }
  
  if (!data || data.length === 0) {
    this.container.innerHTML = '<p class="minor">No data available</p>';
    return;
  }
  
  // Normal rendering
}
```

### API Error Handling
```javascript
try {
  const data = await manager.api('/endpoint');
  await widget.render(data);
} catch (err) {
  manager.showToast(err.message, 'error');
  console.error('Widget load failed:', err);
}
```

---

## Future Enhancements

### Planned Features
1. **Real-time Updates**: WebSocket integration for instant notifications
2. **Drag-drop Kanban**: Full drag-and-drop with status updates
3. **AI Resume Scorer**: Integration with actual resume parsing library
4. **Skill Recommendations**: ML-based skill suggestions
5. **Interview Scheduling**: Calendar integration
6. **Analytics Dashboard**: Career statistics and insights
7. **Export Functionality**: Download reports and resumes
8. **Dark Mode**: Already included!

---

**Last Updated:** March 2025
**Version:** 1.0
**Maintainer:** Placement Portal Team
