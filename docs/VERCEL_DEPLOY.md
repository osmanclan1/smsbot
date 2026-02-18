# Vercel Deployment Guide

## Quick Deploy

### Option 1: Via Vercel CLI (Recommended)

```bash
# Install Vercel CLI (if not installed)
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

### Option 2: Via Vercel Dashboard

1. Go to https://vercel.com
2. Click "Add New Project"
3. Import your Git repository (or drag & drop the `admin/dist` folder)
4. Configure:
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build:admin`
   - **Output Directory**: `admin/dist`
   - **Install Command**: `npm ci`
5. Add Environment Variable:
   - `VITE_API_BASE_URL` = `https://wsb8nu652d.execute-api.us-east-1.amazonaws.com/Prod`
6. Click "Deploy"

## Environment Variables

Set in Vercel Dashboard → Project Settings → Environment Variables:

- `VITE_API_BASE_URL` = `https://wsb8nu652d.execute-api.us-east-1.amazonaws.com/Prod`

## Configuration

The `vercel.json` file is already configured with:
- ✅ Build command: `npm run build:admin`
- ✅ Output directory: `admin/dist`
- ✅ Rewrite rules for routing
- ✅ Security headers

## After Deployment

1. Vercel will provide a URL like: `https://your-project.vercel.app`
2. Test the login page
3. The frontend will automatically use the Lambda API endpoint

## Custom Domain (Optional)

1. Go to Vercel Dashboard → Project → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions



