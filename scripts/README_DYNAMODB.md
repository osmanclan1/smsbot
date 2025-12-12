# Creating DynamoDB Tables

## Option 1: Using the Shell Script (Easiest)

```bash
# Make sure AWS credentials are configured
aws configure

# Run the script
./scripts/create_conversations_table.sh

# Or create all tables
./scripts/create_dynamodb_tables.sh
```

## Option 2: Using AWS CLI Directly

### Create Conversations Table Only

```bash
aws dynamodb create-table \
  --table-name smsbot-conversations \
  --attribute-definitions \
    AttributeName=conversation_id,AttributeType=S \
    AttributeName=phone_number,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema \
    AttributeName=conversation_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes \
    "IndexName=PhoneNumberIndex,KeySchema=[{AttributeName=phone_number,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
  --region us-east-1
```

### Create Using JSON File

```bash
aws dynamodb create-table \
  --cli-input-json file://scripts/create_conversations_table.json \
  --region us-east-1
```

## Verify Tables Were Created

```bash
# List all tables
aws dynamodb list-tables --region us-east-1

# Describe the table
aws dynamodb describe-table \
  --table-name smsbot-conversations \
  --region us-east-1
```

## If Table Already Exists

If you get an error that the table already exists:

```bash
# Delete and recreate (⚠️ WARNING: This deletes all data!)
aws dynamodb delete-table \
  --table-name smsbot-conversations \
  --region us-east-1

# Wait for deletion
aws dynamodb wait table-not-exists \
  --table-name smsbot-conversations \
  --region us-east-1

# Then run create script again
```

## Table Schema

### smsbot-conversations

- **Primary Key:** `conversation_id` (String, UUID)
- **GSI:** `PhoneNumberIndex`
  - Partition Key: `phone_number`
  - Sort Key: `created_at`
- **Billing:** PAY_PER_REQUEST (on-demand)

### Attributes

- `conversation_id` (String) - Primary key
- `phone_number` (String) - Student phone number
- `created_at` (String) - ISO timestamp
- `updated_at` (String) - ISO timestamp
- `status` (String) - "active", "completed", "escalated"
- `messages` (List) - Array of message objects
- `trigger_type` (String, optional) - Type of trigger
- `trigger_id` (String, optional) - Trigger ID

## Troubleshooting

### "Security token is invalid"
- Run `aws configure` to set up credentials
- Make sure your AWS credentials have DynamoDB permissions

### "Table already exists"
- Use `describe-table` to check current schema
- If schema matches, you're good to go!
- If you need to recreate, delete first (⚠️ loses data)

### "Access Denied"
- Your AWS user needs `dynamodb:CreateTable` permission
- Add to IAM policy if needed

