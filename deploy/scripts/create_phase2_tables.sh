#!/bin/bash
# Script to create Phase 2 DynamoDB tables using AWS CLI

set -e

echo "Creating Phase 2 DynamoDB tables..."

# Students Table
echo "Creating smsbot-students table..."
aws dynamodb create-table \
  --table-name smsbot-students \
  --attribute-definitions AttributeName=phone_number,AttributeType=S \
  --key-schema AttributeName=phone_number,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 || echo "Table may already exist"

# Deadlines Table
echo "Creating smsbot-deadlines table..."
aws dynamodb create-table \
  --table-name smsbot-deadlines \
  --attribute-definitions \
    AttributeName=deadline_id,AttributeType=S \
    AttributeName=category,AttributeType=S \
    AttributeName=date,AttributeType=S \
  --key-schema AttributeName=deadline_id,KeyType=HASH \
  --global-secondary-indexes \
    "IndexName=CategoryIndex,KeySchema=[{AttributeName=category,KeyType=HASH},{AttributeName=date,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 || echo "Table may already exist"

# Followups Table
echo "Creating smsbot-followups table..."
aws dynamodb create-table \
  --table-name smsbot-followups \
  --attribute-definitions \
    AttributeName=followup_id,AttributeType=S \
    AttributeName=phone_number,AttributeType=S \
    AttributeName=followup_date,AttributeType=S \
    AttributeName=status,AttributeType=S \
  --key-schema AttributeName=followup_id,KeyType=HASH \
  --global-secondary-indexes \
    "IndexName=PhoneNumberIndex,KeySchema=[{AttributeName=phone_number,KeyType=HASH},{AttributeName=followup_date,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
    "IndexName=StatusDateIndex,KeySchema=[{AttributeName=status,KeyType=HASH},{AttributeName=followup_date,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 || echo "Table may already exist"

echo ""
echo "Waiting for tables to be created..."
aws dynamodb wait table-exists --table-name smsbot-students --region us-east-1
aws dynamodb wait table-exists --table-name smsbot-deadlines --region us-east-1
aws dynamodb wait table-exists --table-name smsbot-followups --region us-east-1

echo ""
echo "✓ All Phase 2 tables created successfully!"

