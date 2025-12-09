# 🚀 Quick Deployment Checklist for Task Buddy

## ✅ Pre-Deployment Checklist
- [ ] All features tested locally
- [ ] Admin account works (kalanadenuz@gmail.com / 12345678)
- [ ] Database is in instance/tasks.db
- [ ] .gitignore includes .env and *.db files
- [ ] requirements.txt is up to date

## 📝 Step-by-Step Commands

### 1️⃣ Initialize Git (if not done)
```powershell
git init
```

### 2️⃣ Add All Files
```powershell
git add .
```

### 3️⃣ Create First Commit
```powershell
git commit -m "Initial commit - Task Buddy with AI prioritization and admin dashboard"
```

### 4️⃣ Create GitHub Repository
- Go to: https://github.com/new
- Name: task-buddy
- Public/Private: Your choice
- DO NOT initialize with README
- Click "Create repository"

### 5️⃣ Connect to GitHub
```powershell
# Replace YOUR-USERNAME with your GitHub username!
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/task-buddy.git
git push -u origin main
```

### 6️⃣ Create Database on Render
- Go to: https://render.com/dashboard
- Click: New + → PostgreSQL
- Name: task-buddy-db
- Plan: Free
- Click: Create Database
- COPY the "Internal Database URL"

### 7️⃣ Deploy Web Service on Render
- Click: New + → Web Service
- Connect GitHub repository: task-buddy
- Settings:
  * Name: task-buddy
  * Environment: Python 3
  * Build Command: pip install -r requirements.txt
  * Start Command: gunicorn server:app
  * Plan: Free
- Add Environment Variables:
  * DATABASE_URL = (paste the Internal Database URL)
  * SECRET_KEY = TaskBuddy2024SecureKey!@#$%ProductionReady
- Click: Create Web Service

### 8️⃣ Wait for Deployment
- Takes ~5-10 minutes
- Watch logs for "✅ Admin account created"
- Copy your app URL when ready

### 9️⃣ Update Frontend URLs
You need to update API URLs in these files:
- script.js
- login.html  
- register.html
- admin.html

Find: http://127.0.0.1:5000
Replace with: https://your-app-name.onrender.com

### 🔟 Push Updates
```powershell
git add .
git commit -m "Update API URLs for production"
git push origin main
```

Wait ~2-3 minutes for auto-redeploy!

## 🎉 You're Live!

Share with friends:
- Register: https://your-app-name.onrender.com/register.html
- Login: https://your-app-name.onrender.com/login.html

Admin access:
- Email: kalanadenuz@gmail.com
- Password: 12345678
- Dashboard: https://your-app-name.onrender.com/admin.html

## 🔄 Future Updates

Whenever you make changes:
```powershell
git add .
git commit -m "Your change description"
git push origin main
```

Render will automatically redeploy!

## ⚠️ Important Notes

1. **Free Tier Sleep**: App sleeps after 15 min of inactivity
   - First load after sleep takes ~50 seconds
   
2. **Database Expiry**: Free database expires after 90 days
   - Backup your data before expiry!
   
3. **Admin Password**: Change it after first deployment for security

4. **Custom Domain**: You can add a custom domain in Render settings (optional)

## 📊 Monitoring

- **Logs**: Render Dashboard → Your Service → Logs
- **Metrics**: Render Dashboard → Your Service → Metrics  
- **Database**: Render Dashboard → Database → Connections
- **Admin Dashboard**: Your app URL + /admin.html

## 🆘 Quick Fixes

**App not loading?**
- Check Render logs for errors
- Verify DATABASE_URL is set correctly

**Can't login?**
- Clear browser cache and cookies
- Check if you're using HTTPS (not HTTP)

**Database errors?**
- Check if database is running in Render dashboard
- Visit /health endpoint to test connection

---

Need help? Check DEPLOYMENT.md for detailed instructions!
