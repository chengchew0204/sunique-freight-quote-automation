# Backend API for Freight Quote System

Flask API backend deployed on Render.com

## Local Development

```bash
cd backend
pip install -r requirements.txt
export INFLOW_COMPANY_ID=your-id
export INFLOW_API_KEY=your-key
export CHR_CLIENT_ID=your-id
export CHR_CLIENT_SECRET=your-secret
export CHR_CUSTOMER_CODE=your-code
export CHR_ENVIRONMENT=sandbox

python app.py
```

## Deployment on Render.com

See `/doc/DEPLOYMENT_GUIDE.md` for full instructions.

## Endpoints

- `GET /health` - Health check
- `POST /api/quote` - Get freight quote

