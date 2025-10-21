# Railway.app Deployment Guide

## Why Railway?
- ✅ **$5/month free credit** (~400+ hours runtime)
- ✅ Fast cold starts (~5 seconds vs 50+ on Render)
- ✅ Automatic deployments from GitHub
- ✅ Built-in domain with HTTPS
- ✅ No sleep after inactivity

## 🚀 Deployment Steps

### Step 1: Create Railway Account

1. Go to [https://railway.app/](https://railway.app/)
2. Click **"Start a New Project"**
3. Sign up with **GitHub** (easiest)

### Step 2: Deploy Backend

1. On Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose: `sunique-shipping-quote-automation`
4. Railway will detect the Python app automatically

### Step 3: Configure Root Directory

Since our backend is in a subdirectory:

1. Click on your deployed service
2. Go to **"Settings"** tab
3. Scroll to **"Service"** section
4. Set **Root Directory** to: `backend`
5. Click **"Save"**

### Step 4: Add Environment Variables

1. Go to **"Variables"** tab
2. Click **"+ New Variable"**
3. Add these 6 variables:

| Variable Name | Value |
|--------------|-------|
| `INFLOW_COMPANY_ID` | `9a253611-78ee-445e-90ed-f6c9f0e7b6fe` |
| `INFLOW_API_KEY` | `41AB3DDAE9DE173187A5AA03DD93326D6C39B22AE02B8593E361F165AACCBFBD-1` |
| `CHR_CLIENT_ID` | `0oa1lgb53s0akheuz358` |
| `CHR_CLIENT_SECRET` | `jxg4xTQHZJAiWTfA79HObvUlHUgJS4gs6u86N8HeCM9PMBTezJU1MZj9Hea2rGI1` |
| `CHR_CUSTOMER_CODE` | `C8827059` |
| `CHR_ENVIRONMENT` | `sandbox` |

4. Variables are automatically saved

### Step 5: Redeploy

1. After adding variables, Railway will auto-redeploy
2. Or manually trigger: **Settings** → **Redeploy**
3. Watch the **Deployment Logs**
4. Wait for: ✅ **"Success"**

### Step 6: Get Your URL

1. Go to **"Settings"** tab
2. Scroll to **"Domains"** section
3. Click **"Generate Domain"**
4. Copy the URL (looks like: `https://your-app.railway.app`)

### Step 7: Update Frontend

Update `script.js` with your Railway URL:

```javascript
const CONFIG = {
    apiEndpoint: 'https://your-app.railway.app/api/quote'
};
```

Then push to GitHub:
```bash
git add script.js
git commit -m "Update API endpoint to Railway"
git push
```

Netlify will auto-deploy the updated frontend.

## ✅ Testing

### Test Backend Health:
```
https://your-app.railway.app/health
```

Expected:
```json
{"status": "healthy", "service": "freight-quote-api"}
```

### Test Full System:
```
https://sunique-shipping-quote-automation.netlify.app
```

Fill out the form and submit - should work with **fast response times**!

## 📊 Monitoring

**View Logs:**
1. Click on your service
2. Go to **"Deployments"** tab
3. Click on latest deployment
4. View real-time logs

**Check Usage:**
1. Go to **"Usage"** tab
2. See how much of your $5 credit is used
3. ~$0.01/hour runtime cost

## 🎯 Performance Comparison

| Platform | Cold Start | Warm Request | Monthly Cost |
|----------|------------|--------------|--------------|
| **Railway** | ~5s | 1-2s | $5 free credit |
| Render Free | 50s+ | 2-5s | Free (but slow) |
| Render Paid | None | 1-2s | $7/month |

## 💡 Tips

1. **Keep service alive**: Railway doesn't sleep like Render free tier
2. **Auto-deploy**: Push to GitHub = automatic deployment
3. **Logs**: Check logs for debugging (very detailed)
4. **Custom domain**: Can add your own domain in Settings

## 🔄 Switching from Render

If you already deployed on Render:
1. Deploy on Railway (follow steps above)
2. Update frontend URL
3. Test on Railway
4. Delete Render service (optional)

Done! Railway is now your backend. 🚀

---

**Deployment Time**: ~5 minutes  
**Performance**: Much faster than Render free tier  
**Cost**: $5/month free credit (400+ hours)

