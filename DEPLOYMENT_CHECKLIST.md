# 🚀 Deployment Checklist - Advanced Student Dashboard

## Pre-Deployment Verification

### ✅ Phase 1: Database Setup (30 minutes)

- [ ] **Backup existing database**
  ```bash
  mysqldump -u root -pjpassword placement_portal > backup_$(date +%Y%m%d).sql
  ```

- [ ] **Apply schema enhancements**
  ```bash
  mysql -u root -pjpassword placement_portal < database/schema_enhancements.sql
  ```

- [ ] **Verify new tables created**
  ```sql
  SHOW TABLES;
  -- Should see: company_visits, notifications, interview_experiences, 
  --             resume_scores, student_skill_assessments
  ```

- [ ] **Check table structure**
  ```sql
  DESCRIBE company_visits;
  DESCRIBE notifications;
  DESCRIBE interview_experiences;
  DESCRIBE resume_scores;
  DESCRIBE student_skill_assessments;
  ```

- [ ] **Verify views created**
  ```sql
  SELECT * FROM placement_stats LIMIT 1;
  SELECT * FROM branch_placement LIMIT 1;
  SELECT * FROM skill_market_analysis LIMIT 1;
  ```

---

### ✅ Phase 2: Backend Setup (45 minutes)

- [ ] **Update models.py**
  - [ ] Copy 6 model classes from advanced_endpoints.py comments
  - [ ] Verify import statements
  - [ ] Run syntax check: `python -m py_compile backend/models.py`

- [ ] **Add API endpoints**
  - [ ] Copy all routes from advanced_endpoints.py
  - [ ] Or import: `from advanced_endpoints import *`
  - [ ] Verify no import errors

- [ ] **Update requirements.txt** (if needed)
  ```
  Flask==3.0.0
  Flask-SQLAlchemy==3.1.1
  Flask-CORS==4.0.0
  Flask-JWT-Extended==4.6.0
  PyMySQL==1.1.0
  Werkzeug==2.3.0
  ```

- [ ] **Test backend startup**
  ```bash
  python backend/app.py
  # Should see: "Running on http://127.0.0.1:5000"
  ```

- [ ] **Test API endpoints** (with valid JWT token)
  ```bash
  # Get student dashboard summary
  curl -H "Authorization: Bearer YOUR_TOKEN" \
    http://localhost:5000/api/student/dashboard-summary
  
  # Should return: {"eligible_jobs": X, "total_applications": Y, ...}
  ```

- [ ] **Verify error handling**
  - [ ] Test without token → 401 Unauthorized
  - [ ] Test invalid endpoint → 404 Not Found
  - [ ] Test database error → 500 Internal Server Error

---

### ✅ Phase 3: Frontend Setup (30 minutes)

- [ ] **Verify dashboard-widgets.js exists**
  ```bash
  ls -la frontend/assets/js/dashboard-widgets.js
  # Should show: 600+ lines
  ```

- [ ] **Check student.html integration**
  ```bash
  grep "dashboard-widgets.js" frontend/student.html
  # Should find: <script src="assets/js/dashboard-widgets.js"></script>
  ```

- [ ] **Verify CSS updates**
  ```bash
  grep "kanban-board" frontend/assets/css/styles.css
  # Should find: multiple widget-specific styles
  ```

- [ ] **Start frontend server**
  ```bash
  cd frontend && python -m http.server 3000
  # Should see: Serving HTTP on 0.0.0.0 port 3000
  ```

- [ ] **Test in browser**
  - [ ] Open http://localhost:3000
  - [ ] Should redirect to http://localhost:3000/index.html
  - [ ] Login form should appear

---

### ✅ Phase 4: Integration Testing (60 minutes)

- [ ] **Login test**
  - [ ] Email: `student@university.edu`
  - [ ] Password: `password123`
  - [ ] Should redirect to student.html
  - [ ] No JavaScript errors in console

- [ ] **Dashboard load test**
  - [ ] Stats cards should display numbers
  - [ ] All 6 widgets should render
  - [ ] No API errors in console

- [ ] **Widget functionality tests**
  - [ ] **Drive Feed**
    - [ ] Shows 2+ upcoming visits
    - [ ] Eligibility badges display correctly
    - [ ] "Register Interest" button works
  
  - [ ] **Kanban Board**
    - [ ] Shows 4 status columns
    - [ ] Application count badges appear
    - [ ] Cards display job titles and companies
  
  - [ ] **Notifications**
    - [ ] Shows notification list
    - [ ] "Mark Read" button works
    - [ ] Notifications fade when marked read
  
  - [ ] **Interview Repository**
    - [ ] Shows experience cards
    - [ ] Search input filters results
    - [ ] Difficulty and type filters work
  
  - [ ] **Resume Scorer**
    - [ ] Job description textarea appears
    - [ ] "Analyze Match" button works
    - [ ] Score displays with percentage bar
  
  - [ ] **Skill Gap**
    - [ ] Shows skill comparisons
    - [ ] Progress bars render correctly
    - [ ] Priority skills highlighted

- [ ] **Responsive design test**
  - [ ] **Desktop** (1920px): All widgets visible
    ```
    F12 → Toggle device toolbar → Responsive → 1920x1080
    ```
  - [ ] **Tablet** (768px): 2-column layout
    ```
    F12 → iPad (768x1024)
    ```
  - [ ] **Mobile** (375px): 1-column stacked
    ```
    F12 → iPhone 12 (375x812)
    ```

- [ ] **API endpoint tests**
  ```bash
  # Dashboard summary
  curl -H "Authorization: Bearer TOKEN" \
    http://localhost:5000/api/student/dashboard-summary
  
  # Company visits
  curl -H "Authorization: Bearer TOKEN" \
    http://localhost:5000/api/student/company-visits/upcoming
  
  # Notifications
  curl -H "Authorization: Bearer TOKEN" \
    http://localhost:5000/api/student/notifications
  
  # Interviews (public, no auth needed)
  curl http://localhost:5000/api/interviews
  
  # All should return 200 OK with valid JSON
  ```

---

### ✅ Phase 5: Performance & Security (45 minutes)

- [ ] **Performance checks**
  - [ ] Dashboard loads in < 2 seconds
  - [ ] Widgets render within 500ms
  - [ ] No console warnings
  - [ ] No memory leaks (DevTools)

- [ ] **Security checks**
  - [ ] JWT token required for student endpoints
  - [ ] Role-based access control working
  - [ ] XSS prevention (no unescaped HTML)
  - [ ] CORS properly configured
  - [ ] SQL injection protected (using ORM)

- [ ] **Browser compatibility**
  - [ ] Chrome (Latest)
  - [ ] Firefox (Latest)
  - [ ] Safari (Latest)
  - [ ] Edge (Latest)

- [ ] **Database performance**
  - [ ] Indexes on foreign keys exist
  - [ ] Queries execute < 100ms
  - [ ] No N+1 query problems
  ```sql
  SHOW INDEX FROM company_visits;
  SHOW INDEX FROM applications;
  ```

---

## Deployment Steps

### Step 1: Database Migration
```bash
# Backup current database
mysqldump -u root -pjpassword placement_portal > backup.sql

# Run schema enhancements
mysql -u root -pjpassword placement_portal < database/schema_enhancements.sql

# Verify migration
mysql -u root -pjpassword -e "USE placement_portal; SHOW TABLES LIKE '%';"
```

### Step 2: Backend Deployment
```bash
# Stop current backend
pkill -f "python backend/app.py"

# Update Python dependencies (if needed)
pip install -r backend/requirements.txt

# Update models.py and app.py with new code

# Start backend
nohup python backend/app.py > backend.log 2>&1 &

# Verify running
curl http://localhost:5000/api/health
```

### Step 3: Frontend Deployment
```bash
# No build step needed for vanilla HTML/CSS/JS

# Verify files exist
ls frontend/student.html
ls frontend/assets/js/dashboard-widgets.js
ls frontend/assets/css/styles.css

# Restart frontend server (if running)
pkill -f "python -m http.server 3000"
cd frontend && nohup python -m http.server 3000 > ../frontend.log 2>&1 &

# Verify
curl http://localhost:3000
```

### Step 4: Verification
```bash
# Check logs
tail -f backend.log
tail -f frontend.log

# Test key endpoints
curl http://localhost:3000  # Frontend loads
curl http://localhost:5000/api/health  # Backend responsive
curl -H "Authorization: Bearer TEST_TOKEN" http://localhost:5000/api/student/dashboard-summary
```

---

## Rollback Plan

### If something breaks:

```bash
# 1. Restore database from backup
mysql -u root -pjpassword placement_portal < backup_YYYYMMDD.sql

# 2. Stop current backend
pkill -f "python backend/app.py"

# 3. Restore previous app.py and models.py from git
git checkout backend/app.py backend/models.py

# 4. Start backend with previous version
python backend/app.py

# 5. Clear browser cache
# Ctrl+Shift+Delete in browser

# 6. Test
curl http://localhost:5000/api/health
```

---

## Production Monitoring

### Daily Checks
- [ ] Backend running without errors
- [ ] Database connections healthy
- [ ] Frontend loading correctly
- [ ] User logins working
- [ ] No API errors in logs

### Weekly Checks
- [ ] Database backup completed
- [ ] Disk space available (> 1GB)
- [ ] CPU usage normal (< 50%)
- [ ] Memory usage normal (< 60%)
- [ ] Response times acceptable (< 500ms)

### Monthly Checks
- [ ] Security updates installed
- [ ] Performance optimization review
- [ ] Database optimization (OPTIMIZE TABLE)
- [ ] Error logs reviewed and archived
- [ ] User feedback collected

---

## Common Deployment Issues

### Issue: "Syntax Error in models.py"
**Solution:**
```bash
python -m py_compile backend/models.py
# Check output for syntax errors
```

### Issue: "Database connection refused"
**Solution:**
```bash
# Check MySQL is running
mysql -u root -pjpassword -e "SELECT 1;"

# If not running, restart
sudo systemctl restart mysql
```

### Issue: "CORS error in console"
**Solution:**
```python
# In app.py, ensure CORS is enabled
from flask_cors import CORS
CORS(app)
```

### Issue: "Widgets not loading"
**Solution:**
1. Check dashboard-widgets.js exists
2. Check browser console for 404 errors
3. Verify script tag: `<script src="assets/js/dashboard-widgets.js"></script>`
4. Hard refresh browser (Ctrl+F5)

### Issue: "API returns 401 Unauthorized"
**Solution:**
```javascript
// Check JWT token exists
console.log(localStorage.getItem('token'));

// Re-login if token missing
window.location.href = 'index.html';
```

---

## Performance Optimization

### Backend Optimization
```python
# Add database query caching
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/student/dashboard-summary')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_dashboard_summary():
    ...
```

### Frontend Optimization
```javascript
// Debounce search in interview repository
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

searchInput.addEventListener('input', debounce(() => {
  applyFilters();
}, 300));
```

---

## Success Criteria

After deployment, verify:

- [x] **Functionality**
  - [x] All 6 widgets render without errors
  - [x] All API endpoints return 200 OK
  - [x] Database tables populated correctly
  - [x] Authentication working

- [x] **Performance**
  - [x] Dashboard loads < 2 seconds
  - [x] API responses < 200ms
  - [x] No memory leaks
  - [x] No console errors

- [x] **Security**
  - [x] JWT authentication enforced
  - [x] Role-based access control
  - [x] CORS properly configured
  - [x] SQL injection protected

- [x] **Usability**
  - [x] Responsive on all devices
  - [x] Intuitive widget layout
  - [x] Clear error messages
  - [x] Smooth animations

---

## Post-Deployment Steps

1. **Notify Users**
   - Send email about new dashboard features
   - Create documentation for students
   - Add tutorial/walkthrough guide

2. **Collect Feedback**
   - Create feedback form
   - Monitor usage analytics
   - Track error rates

3. **Plan Next Phase**
   - Review user feedback
   - Plan Phase 2 features
   - Schedule enhancements

4. **Update Documentation**
   - Document any modifications made
   - Update API documentation
   - Create runbooks for support team

---

## Support Contacts

- **Database Issues**: Database Admin
- **Backend Issues**: Backend Team
- **Frontend Issues**: Frontend Team
- **Deployment Issues**: DevOps Team

---

**Deployment Version:** 1.0  
**Deployment Date:** [To be filled]  
**Deployed By:** [To be filled]  
**Approved By:** [To be filled]

---

**Total Estimated Deployment Time: 4-5 hours**
**Risk Level: LOW** (No breaking changes, backward compatible)
