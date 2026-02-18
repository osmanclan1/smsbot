#!/bin/bash
# Script to create ONLY the Conversations table for SMS Bot

set -e

REGION=${AWS_REGION:-us-east-1}

echo "Creating Conversations Table in region: $REGION"
echo ""

# Create Conversations Table
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
  --region $REGION

echo ""
echo "Waiting for table to be active..."
aws dynamodb wait table-exists \
  --table-name smsbot-conversations \
  --region $REGION

echo ""
echo "✓ Conversations table created successfully!"
echo ""
echo "Table: smsbot-conversations"
echo "  - Primary Key: conversation_id (String)"
echo "  - GSI: PhoneNumberIndex (phone_number + created_at)"
echo "  - Billing: PAY_PER_REQUEST (on-demand)"

