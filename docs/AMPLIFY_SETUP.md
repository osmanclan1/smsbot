# AWS Amplify Deployment Guide

## Quick Setup via AWS Console (Recommended)

1. **Go to AWS Amplify Console**: https://console.aws.amazon.com/amplify
2. **Click "New app" → "Host web app"**
3. **Connect your Git repository** (GitHub, GitLab, Bitbucket, or AWS CodeCommit)
   - Or choose "Deploy without Git" and upload the built files manually
4. **Configure build settings**:
   - Build command: `npm ci && npm run build:admin`
   - Output directory: `admin/dist`
5. **Add environment variables**:
   - `VITE_API_BASE_URL`: `https://wsb8nu652d.execute-api.us-east-1.amazonaws.com/Prod`
6. **Review and deploy**

## Manual Deployment via CLI

If you prefer CLI:

```bash
# Initialize Amplify (if not already done)
amplify init

# Add hosting
amplify add hosting

# Deploy
amplify publish
```

## Environment Variables

Set these in Amplify Console → App Settings → Environment variables:

- `VITE_API_BASE_URL`: `https://wsb8nu652d.execute-api.us-east-1.amazonaws.com/Prod`

## Current Configuration

- **API Endpoint**: `https://wsb8nu652d.execute-api.us-east-1.amazonaws.com/Prod`
- **Build Config**: `amplify.yml` (already created)
- **Frontend**: Admin dashboard ready for deployment

## Notes

- The frontend will automatically detect if it's running on Amplify and use the Lambda API
- CORS is already configured on the Lambda API to allow requests from any origin
- The build process creates optimized production files in `admin/dist`



