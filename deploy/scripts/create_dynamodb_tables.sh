#!/bin/bash
# Script to create DynamoDB tables for SMS Bot

set -e

REGION=${AWS_REGION:-us-east-1}

echo "Creating DynamoDB tables in region: $REGION"
echo ""

# Create Conversations Table
echo "Creating Conversations Table..."
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

echo "Waiting for Conversations table to be active..."
aws dynamodb wait table-exists \
  --table-name smsbot-conversations \
  --region $REGION

echo "✓ Conversations table created successfully!"
echo ""

# Create Triggers Table (for future use)
echo "Creating Triggers Table..."
aws dynamodb create-table \
  --table-name smsbot-triggers \
  --attribute-definitions \
    AttributeName=trigger_id,AttributeType=S \
    AttributeName=phone_number,AttributeType=S \
  --key-schema \
    AttributeName=trigger_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes \
    "IndexName=PhoneNumberIndex,KeySchema=[{AttributeName=phone_number,KeyType=HASH}],Projection={ProjectionType=ALL}" \
  --region $REGION

echo "Waiting for Triggers table to be active..."
aws dynamodb wait table-exists \
  --table-name smsbot-triggers \
  --region $REGION

echo "✓ Triggers table created successfully!"
echo ""

# Create Results Table (for future use)
echo "Creating Results Table..."
aws dynamodb create-table \
  --table-name smsbot-results \
  --attribute-definitions \
    AttributeName=result_id,AttributeType=S \
    AttributeName=conversation_id,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema \
    AttributeName=result_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes \
    "IndexName=ConversationIndex,KeySchema=[{AttributeName=conversation_id,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
  --region $REGION

echo "Waiting for Results table to be active..."
aws dynamodb wait table-exists \
  --table-name smsbot-results \
  --region $REGION

echo "✓ Results table created successfully!"
echo ""
echo "All tables created successfully!"
echo ""
echo "Tables created:"
echo "  - smsbot-conversations"
echo "  - smsbot-triggers"
echo "  - smsbot-results"

