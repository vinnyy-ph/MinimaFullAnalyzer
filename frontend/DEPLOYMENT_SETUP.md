# Frontend Deployment Setup

## Environment Variables for Production

When deploying to Vercel, you need to set the following environment variable:

### In Vercel Dashboard:
1. Go to your project settings in Vercel
2. Navigate to "Environment Variables"
3. Add:
   - **Name**: `REACT_APP_API_URL`
   - **Value**: `https://minima-backend.onrender.com`
   - **Environment**: Production (and Preview if you want)

### For Local Development:
Create a `.env.local` file in the `frontend` directory with:
```
REACT_APP_API_URL=http://localhost:5000
```

This will ensure your app uses the correct backend URL in each environment. 