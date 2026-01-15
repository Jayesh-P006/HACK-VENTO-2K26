# 🚀 URGENT: Deploy Backend Fixes

## Issues Fixed
1. ✅ Removed duplicate `/api/health` endpoint that was causing:
   ```
   AssertionError: View function mapping is overwriting an existing endpoint function: health_check
   ```

2. ✅ Fixed Department model seeding error:
   ```
   'full_name' is an invalid keyword argument for Department
   ```
   - Changed to use valid fields: `code` and `description`

3. ✅ Updated CORS configuration to allow all routes (`/*` instead of `/api/*` only)
   - Fixes CORS preflight errors
   - Allows frontend to access `/api/health`, `/api/batches/active`, etc.

## Deploy Steps

### Option 1: Git Push (Recommended)
```bash
cd "f:\2. HACKVENTO 2K26"
git add backend/app.py
git commit -m "Fix: Remove duplicate health endpoint, fix Department seeding, update CORS"
git push origin main
```

Railway will automatically redeploy.

### Option 2: Railway CLI
```bash
cd "f:\2. HACKVENTO 2K26"
railway up
```

### Option 3: Railway Dashboard
1. Go to https://railway.app/dashboard
2. Select your project
3. Click on the backend service
4. Go to "Deployments" tab
5. Click "Redeploy" button

## Verification After Deployment

1. **Check health endpoint:**
   ```
   https://hack-vento-2k26-production.up.railway.app/api/health
   ```
   Should return: `{"status": "healthy", "message": "Placement Portal API is running"}`

2. **Check batches endpoint:**
   ```
   https://hack-vento-2k26-production.up.railway.app/api/batches/active
   ```
   Should return: `[]` or array of batch objects

3. **Test registration:**
   - Open https://hack-vento-2k26-toer.vercel.app/portal/register.html
   - Form should load without "Failed to load batches" error
   - Should be able to create account

## Expected Deployment Logs
✅ Good logs:
```
[db] checking for core tables...
[db] seeding departments...
[db] seeding batches...
Starting gunicorn 21.2.0
Listening at: http://0.0.0.0:8080
```

❌ Bad logs (OLD - should not see these anymore):
```
AssertionError: View function mapping is overwriting an existing endpoint function: health_check
'full_name' is an invalid keyword argument for Department
Worker failed to boot
```
