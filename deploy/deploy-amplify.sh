#!/bin/bash
# Script to deploy to AWS Amplify
# This script uploads the built files and starts a deployment

set -e

APP_ID="d1ysf6u09o4y3d"
BRANCH_NAME="main"
REGION="us-east-1"
ZIP_FILE="amplify-deploy.zip"

echo "🚀 Starting Amplify deployment..."

# Step 1: Create deployment and get upload URL
echo "📦 Creating deployment..."
DEPLOY_INFO=$(aws amplify create-deployment \
  --app-id $APP_ID \
  --branch-name $BRANCH_NAME \
  --region $REGION \
  --output json)

JOB_ID=$(echo $DEPLOY_INFO | jq -r '.jobSummary.jobId')
ZIP_URL=$(echo $DEPLOY_INFO | jq -r '.zipUploadUrl')

echo "✅ Deployment created - Job ID: $JOB_ID"
echo "📤 Upload URL obtained"

# Step 2: Upload zip file
echo "⬆️  Uploading files..."
curl -X PUT "$ZIP_URL" \
  --upload-file $ZIP_FILE \
  --silent \
  --show-error

if [ $? -eq 0 ]; then
  echo "✅ Upload successful"
else
  echo "❌ Upload failed"
  exit 1
fi

# Step 3: Start deployment
echo "🚀 Starting deployment..."
aws amplify start-deployment \
  --app-id $APP_ID \
  --branch-name $BRANCH_NAME \
  --job-id $JOB_ID \
  --region $REGION

echo "✅ Deployment started!"
echo ""
echo "📊 Monitor deployment at:"
echo "   https://console.aws.amazon.com/amplify/home?region=$REGION#/$APP_ID/$BRANCH_NAME"
echo ""
echo "🌐 Your app will be available at:"
echo "   https://$BRANCH_NAME.$APP_ID.amplifyapp.com"



