# Sunique Freight Quote System

Modern web application for calculating freight shipping quotes with automated pallet optimization and carrier rate comparison.

## Quick Start

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial deployment"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy on Netlify**: Connect GitHub repo at [netlify.com](https://netlify.com)

3. **Set Environment Variables** in Netlify dashboard:
   - `INFLOW_COMPANY_ID`
   - `INFLOW_API_KEY`
   - `CHR_CLIENT_ID`
   - `CHR_CLIENT_SECRET`
   - `CHR_CUSTOMER_CODE`
   - `CHR_ENVIRONMENT` (sandbox/production)

4. **Trigger Deploy** and test with an order from today

📖 **Full documentation**: See `/doc` folder

## Architecture

- **Frontend**: Static HTML/CSS/JavaScript
- **Backend**: Netlify Serverless Functions (Python 3.9)
- **APIs**: inFlow Inventory, C.H. Robinson
- **Hosting**: Netlify (single deployment)

## Project Structure

```
development-website/
├── index.html                # Frontend UI
├── script.js                 # Frontend logic
├── styles.css                # UI styling
├── netlify.toml              # Netlify config
├── data/                     # Frontend assets
├── netlify/functions/        # Backend (Python)
│   ├── quote.py             # Main API endpoint
│   ├── lib/                 # Business logic
│   └── data/                # Product dimensions
└── doc/                      # Documentation
```

## Documentation

- **Deployment Guide**: `/doc/DEPLOYMENT_GUIDE.md` - Step-by-step deployment instructions
- **Architecture**: `/doc/NETLIFY_DEPLOYMENT.md` - Technical architecture details
- **Implementation**: `/doc/IMPLEMENTATION_SUMMARY.md` - Complete migration summary

## Features

- ✅ Modern responsive UI with progress tracking
- ✅ Automatic order fetching from inFlow
- ✅ Smart pallet optimization (standard & long pallets)
- ✅ Freight class calculation
- ✅ C.H. Robinson quote integration
- ✅ Intelligent markup (20% or 30%)

## Local Development

```bash
npm install -g netlify-cli
netlify dev
```

Visit `http://localhost:8888`

## Support

Check function logs in Netlify Dashboard → Functions → quote

---

**Version**: 1.1.0 (Production Environment)

**Current Environment**: Production C.H. Robinson API

