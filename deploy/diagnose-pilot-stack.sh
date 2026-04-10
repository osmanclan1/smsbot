#!/usr/bin/env bash
# Print CloudFormation / change-set diagnostics for pilot stacks (us-east-1).
# Usage: from repo root, after: source .env && unset AWS_ACCESS_KEY_* AWS_SESSION_TOKEN (if using SSO)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[[ -f "$ROOT/.env" ]] && set -a && source "$ROOT/.env" && set +a
[[ -n "${AWS_PROFILE:-}" ]] && unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN || true
REGION="${AWS_REGION:-us-east-1}"
STACK="${1:-smsbot-pilot-v1-stack}"

echo "=== sts get-caller-identity ==="
aws sts get-caller-identity --output json
echo
echo "=== describe-stacks $STACK ==="
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --query 'Stacks[0].[StackName,StackStatus,StackStatusReason]' --output text 2>&1 || true
echo
echo "=== list-change-sets (latest StatusReason) ==="
aws cloudformation list-change-sets --stack-name "$STACK" --region "$REGION" --query 'Summaries[0].[ChangeSetName,Status,StatusReason]' --output text 2>&1 || true
echo
echo "=== recent stack events ==="
aws cloudformation describe-stack-events --stack-name "$STACK" --region "$REGION" --max-items 15 --query 'StackEvents[*].[Timestamp,ResourceStatus,LogicalResourceId,ResourceStatusReason]' --output table 2>&1 || true
