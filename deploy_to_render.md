# Complete Render Deployment Guide for RohiniGH2

## Step 1: Create GitHub Repository (Do this first!)

**In the browser window that just opened:**
1. Repository name: `customer-segmentation`
2. Description: `Customer Segmentation and Recommendation System`
3. Make sure it's **PUBLIC** (required for free Render)
4. **DO NOT** check any boxes (no README, .gitignore, or license)
5. Click **"Create repository"**

## Step 2: Push Code to GitHub

After creating the repository, run these commands in PowerShell:

```powershell
git push -u origin main
```

If you get authentication errors, GitHub will prompt you to log in.

## Step 3: Deploy to Render

### 3.1 Create Database
1. Go to https://render.com and sign up/log in
2. Click **"New +"** → **"PostgreSQL"**
3. Fill in:
   - Name: `customer-segmentation-db`
   - Database: `dressly_db` 
   - Region: `Oregon (US West)`
   - Plan: **Free**
4. Click **"Create Database"**
5. **COPY THE DATABASE URL** - you'll need it!

### 3.2 Deploy Web Service
1. Click **"New +"** → **"Web Service"**
2. **"Connect a repository"** → Connect your GitHub
3. Select repository: `RohiniGH2/customer-segmentation`
4. Fill in:
   - Name: `customer-segmentation-app`
   - Region: `Oregon (US West)` (same as database)
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

### 3.3 Environment Variables

In the **Environment** section, add:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | `customer_seg_secret_key_2025_production` |
| `DB_HOST` | (extract from database URL) |
| `DB_USER` | (extract from database URL) |
| `DB_PASSWORD` | (extract from database URL) |
| `DB_NAME` | `dressly_db` |
| `DB_PORT` | `5432` |

**To extract database credentials:**
- Database URL format: `postgresql://user:password@host:port/database`
- DB_HOST = the host part
- DB_USER = the user part  
- DB_PASSWORD = the password part

### 3.4 Deploy
Click **"Create Web Service"**

## Step 4: Initialize Database
Once deployed, go to your web service → **Shell** tab and run:
```bash
python migrate_db.py
```

## Your app will be live at:
`https://customer-segmentation-app.onrender.com`

---

**Free Tier Notes:**
- App sleeps after 15 minutes of inactivity
- Takes ~30 seconds to wake up
- 0.1GB database storage limit
- Perfect for portfolio/demo purposes!