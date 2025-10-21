# Netlify Serverless Deployment Plan

## Overview
Deploy the entire Freight Quote System on Netlify using serverless functions for the backend logic.

## Architecture
- **Frontend**: Static HTML/CSS/JS (existing `development-website/`)
- **Backend**: Netlify Serverless Functions (Python)
- **Hosting**: Everything on Netlify (single deployment)

## Directory Structure

```
/02-Shipping/development-web/
├── index.html                    # Frontend (no changes)
├── script.js                     # Update to call /.netlify/functions/
├── styles.css                    # Frontend (no changes)
├── data/
│   ├── logo.png
│   └── product-dimensions.json
├── netlify.toml                  # Netlify configuration
├── netlify/
│   └── functions/
│       ├── quote.py              # Main API endpoint
│       ├── requirements.txt      # Python dependencies
│       ├── lib/
│       │   ├── __init__.py
│       │   ├── pallet_calculator.py
│       │   ├── product_dimensions.py
│       │   ├── inflow_api.py
│       │   ├── chr_auth.py
│       │   ├── freight.py
│       │   └── quote_service.py
│       └── data/
│           └── Product Dimension.xlsx
└── README.md
```

## Implementation

### 1. Netlify Function (API Endpoint)
**File**: `netlify/functions/quote.py`
- Single serverless function endpoint
- Handles POST requests with form data
- Returns complete quote response
- Uses all ported Python logic from `development/main.py`

### 2. Business Logic Modules
**Files in**: `netlify/functions/lib/`
- `pallet_calculator.py` - Pallet optimization algorithm
- `product_dimensions.py` - Load Excel dimensions
- `inflow_api.py` - inFlow API client with retry logic
- `chr_auth.py` - C.H. Robinson authentication
- `freight.py` - Freight class calculation and CHR integration
- `quote_service.py` - Quote selection logic

### 3. Frontend Update
**File**: `script.js`
- Change API base URL to: `/.netlify/functions/quote`
- Remove CORS proxy (not needed with Netlify Functions)
- Keep all UI/UX logic unchanged

### 4. Configuration
**File**: `netlify.toml`
```toml
[build]
  functions = "netlify/functions"
  publish = "."

[functions]
  python_version = "3.9"

[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200
```

**File**: `netlify/functions/requirements.txt`
```
requests==2.31.0
pandas==2.1.3
openpyxl==3.1.2
```

### 5. Environment Variables (Set in Netlify Dashboard)
- `INFLOW_COMPANY_ID`
- `INFLOW_API_KEY`
- `CHR_CLIENT_ID`
- `CHR_CLIENT_SECRET`
- `CHR_CUSTOMER_CODE`

## Benefits of This Approach
✅ Single deployment (frontend + backend together)
✅ No separate backend hosting needed
✅ Netlify handles scaling automatically
✅ Built-in HTTPS and CDN
✅ Environment variables in Netlify dashboard
✅ Free tier sufficient for development

## Deployment Steps
1. Push `development-web/` folder to GitHub
2. Connect GitHub repo to Netlify
3. Set environment variables in Netlify dashboard
4. Deploy automatically

## Key Changes from Flask Plan
- Serverless function instead of Flask app
- No `app.py` or Flask routes
- Single function handles all processing
- No persistent server needed
- Automatic scaling with Netlify

