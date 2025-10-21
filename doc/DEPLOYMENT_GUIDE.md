# Quick Deployment Guide

## 🚀 5-Minute Deployment to Netlify

### Step 1: Push to GitHub

```bash
cd /Users/zackwu204/CursorAI/Sunique/02-Shipping/development-website

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial deployment: Freight quote system"

# Create repository on GitHub first, then:
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Netlify

1. Go to [https://app.netlify.com/](https://app.netlify.com/)
2. Click **"Add new site"** → **"Import an existing project"**
3. Choose **GitHub** (authorize if needed)
4. Select your repository
5. Configure:
   - **Build command**: (leave empty)
   - **Publish directory**: `.`
   - **Functions directory**: `netlify/functions`
6. Click **"Deploy site"**

### Step 3: Set Environment Variables

After deployment, go to **Site settings** → **Build & deploy** → **Environment variables** → **Add variable**:

Add these **8 variables**:

| Key | Value |
|-----|-------|
| `INFLOW_COMPANY_ID` | `9a253611-78ee-445e-90ed-f6c9f0e7b6fe` |
| `INFLOW_API_KEY` | `41AB3DDAE9DE173187A5AA03DD93326D6C39B22AE02B8593E361F165AACCBFBD-1` |
| `CHR_CLIENT_ID` | `0oa1lgb53s0akheuz358` |
| `CHR_CLIENT_SECRET` | `jxg4xTQHZJAiWTfA79HObvUlHUgJS4gs6u86N8HeCM9PMBTezJU1MZj9Hea2rGI1` |
| `CHR_CUSTOMER_CODE` | `C8827059` |
| `CHR_ENVIRONMENT` | `sandbox` |

> **Note**: Use `production` for `CHR_ENVIRONMENT` when ready for live API

### Step 4: Trigger Rebuild

1. Go to **Deploys** tab
2. Click **"Trigger deploy"** → **"Deploy site"**
3. Wait for deployment to complete (~2-3 minutes)

### Step 5: Test

1. Open your site URL (shown in Netlify dashboard)
2. Enter test order:
   - **Order Number**: Any order created today in inFlow
   - **Assembly**: Select Yes or No
   - **Pickup ZIP**: e.g., `91776`
   - **Destination ZIP**: e.g., `10001`
   - **Delivery Type**: Commercial
   - **Pickup Date**: Tomorrow or later
3. Click **"Get Freight Quote"**
4. Should see results within 5-10 seconds

## 🔧 Troubleshooting

### Function Not Working?

**Check Netlify Function Logs:**
1. Netlify Dashboard → **Functions** tab
2. Click **quote** function
3. View logs for errors

**Common Issues:**

| Problem | Solution |
|---------|----------|
| "Environment variables missing" | Verify all 6 env vars are set in Netlify |
| "Order not found" | Order must be created TODAY in inFlow |
| Function timeout | Contact support to increase timeout limit |
| Import errors | Check `netlify/functions/requirements.txt` |

### Still Not Working?

1. **Check environment variables** are saved
2. **Trigger manual redeploy** after adding env vars
3. **View function logs** for specific errors
4. **Test inFlow API** credentials separately
5. **Verify C.H. Robinson** credentials are valid

## 📱 Custom Domain (Optional)

1. Netlify Dashboard → **Domain settings**
2. Click **"Add custom domain"**
3. Follow DNS configuration instructions
4. Free SSL certificate auto-provisioned

## 🔄 Updates

To update the application:

```bash
# Make changes to files
git add .
git commit -m "Description of changes"
git push

# Netlify auto-deploys on push
```

## ⚡ Performance Tips

1. **Cold Start**: First request takes ~3 seconds (serverless function initialization)
2. **Subsequent Requests**: ~2-5 seconds depending on order complexity
3. **Upgrade to Pro**: If you need faster cold starts or longer timeouts

## 📊 Monitoring

**View Usage Stats:**
- Netlify Dashboard → **Analytics** tab
- Function invocations
- Bandwidth usage
- Error rates

**Function Timeout Limits:**
- Free tier: 10 seconds
- Pro tier: 26 seconds
- Enterprise: Custom

## 🎯 Next Steps

- [ ] Test with various order types
- [ ] Monitor function performance
- [ ] Set up alerts for errors
- [ ] Consider custom domain
- [ ] Switch to production CHR API when ready

---

## Need Help?

1. Check [Netlify docs](https://docs.netlify.com/functions/overview/)
2. Review function logs
3. Test APIs individually
4. Verify all environment variables

**Deployment Complete! 🎉**

