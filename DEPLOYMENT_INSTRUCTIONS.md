# DEPLOYMENT_INSTRUCTIONS.md

## 🚀 Deployment Guide

### Prerequisites
- GitHub account
- Railway account (railway.app)
- Vercel account (vercel.com)

---

## Step 1: Deploy Backend to Railway

### 1.1 Create Railway Project
1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub
5. Select this repository
6. Choose the `backend` folder as root directory

### 1.2 Add MySQL Database
1. In your Railway project, click "+ New"
2. Select "Database" → "MySQL"
3. Railway will automatically create a database and provide connection details

### 1.3 Configure Environment Variables
In Railway project settings, add these variables:

```
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-generate-a-strong-one
JWT_SECRET_KEY=your-jwt-secret-here-generate-a-strong-one
DB_HOST=<from Railway MySQL>
DB_USER=<from Railway MySQL>
DB_PASSWORD=<from Railway MySQL>
DB_NAME=<from Railway MySQL>
DB_PORT=3306
GEMINI_API_KEY=your_gemini_api_key_here

# Google Drive (Resume storage)
GOOGLE_SERVICE_ACCOUNT_JSON=...json...
GOOGLE_DRIVE_FOLDER_ID=...

# Google Calendar (Org/shared calendar)
GOOGLE_CALENDAR_ID=...
GROQ_API_KEY=your_groq_api_key_here
```

Railway will auto-populate MySQL variables when you connect the database.

### 1.4 Get Your Backend URL
After deployment, Railway provides a URL like:
`https://your-app.up.railway.app`

**COPY THIS URL - you'll need it for the frontend!**

### 1.5 Initialize Database
After first deployment, run this command in Railway's terminal:
```bash
python init_app_db.py
```

---

## Step 2: Update Frontend with Backend URL

### 2.1 Update API URLs
Replace `your-backend-url.up.railway.app` with your actual Railway URL in these files:
- `frontend/public/portal/assets/js/app.js`
- `frontend/public/portal/assets/js/dashboard-widgets.js`
- `frontend/public/portal/assets/js/hiring-rounds.js`
- `frontend/public/portal/assets/js/config.js`

Search for: `https://your-backend-url.up.railway.app`
Replace with: `https://your-actual-railway-url.up.railway.app`

### 2.2 Commit Changes
```bash
git add .
git commit -m "Update backend URL for production"
git push
```

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Project
1. Go to https://vercel.com
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### 3.2 Deploy
Click "Deploy" - Vercel will build and deploy automatically!

Your frontend will be live at:
`https://your-project.vercel.app`

---

## Step 4: Test Deployment

1. Visit your Vercel URL
2. Go to `/portal/login.html`
3. Login with demo accounts:
   - Admin: admin@university.edu / admin123
   - Student: student@university.edu / student123
   - Company: company@tech.com / company123

---

## ✅ Deployment Complete!

Your application is now live:
- **Frontend**: https://your-project.vercel.app
- **Backend API**: https://your-app.up.railway.app
- **Database**: Hosted on Railway MySQL

---

## Troubleshooting

### CORS Errors
If you see CORS errors, update `backend/app.py`:
```python
CORS(app, resources={r"/api/*": {
    "origins": ["https://your-project.vercel.app"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})
```

### Database Connection Issues
- Check Railway environment variables
- Verify MySQL service is running
- Run database initialization script

### Build Errors
- Ensure all dependencies are in requirements.txt
- Check Railway build logs
- Verify Python version compatibility

---

## Updating Your App

### Backend Updates
1. Push changes to GitHub
2. Railway auto-deploys from main branch

### Frontend Updates
1. Push changes to GitHub
2. Vercel auto-deploys from main branch

---

## Need Help?
- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
