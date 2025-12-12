# AWS Credentials Setup Guide

The bot can use AWS credentials from your `.env` file. This makes it easy to configure without manual setup.

## Quick Setup

1. **Open your `.env` file** (it already exists in the project root)

2. **Add or update your AWS credentials:**

```bash
# Option 1: Direct credentials (recommended for local development)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# Optional: If using temporary credentials
# AWS_SESSION_TOKEN=your_session_token_here
```

3. **Save the file** - credentials are automatically loaded when you start the server

## How It Works

The bot tries credentials in this order:
1. **Direct credentials** from `.env` (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
2. **AWS Profile** from `.env` (AWS_PROFILE)
3. **Default credentials** from `~/.aws/credentials`

## Getting AWS Credentials

### Option 1: IAM User Credentials (Recommended for Development)
1. Go to AWS Console → IAM → Users
2. Create a new user or select existing user
3. Go to "Security credentials" tab
4. Click "Create access key"
5. Copy the Access Key ID and Secret Access Key
6. Add them to your `.env` file

### Option 2: Temporary Credentials (If using AWS SSO)
1. Run: `aws sso login --profile your-profile`
2. Run: `aws configure export-credentials --profile your-profile --format env`
3. Copy the output to your `.env` file

### Option 3: Use AWS Profile
If you have AWS CLI configured:
```bash
# In .env file:
AWS_PROFILE=your-profile-name
AWS_REGION=us-east-1
```

## Security Notes

- ✅ `.env` is already in `.gitignore` - your credentials won't be committed
- ✅ Never commit credentials to git
- ✅ Rotate credentials regularly
- ✅ Use IAM roles with least privilege

## Testing Your Credentials

After updating `.env`, test with:
```bash
python -c "from src.storage.dynamodb import DynamoDBService; db = DynamoDBService(); print('✅ AWS credentials working!')"
```

## Troubleshooting

**Error: "ExpiredToken"**
- Your credentials have expired
- Update `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`
- If using temporary credentials, also update `AWS_SESSION_TOKEN`

**Error: "InvalidClientTokenId"**
- Your credentials are incorrect
- Double-check the values in `.env` (no extra spaces, correct format)

**Error: "ResourceNotFoundException"**
- Credentials work, but the DynamoDB table doesn't exist
- Run: `bash scripts/create_dynamodb_tables.sh`
- Or create tables manually in AWS Console

## Running Without AWS

The bot can run in "limited mode" without AWS credentials:
- ✅ All 6 easy-win features work
- ✅ Knowledge base queries work
- ✅ SMS responses work
- ❌ Conversations won't be saved to DynamoDB
- ❌ Profile collection won't save

This is useful for testing features without setting up AWS.

