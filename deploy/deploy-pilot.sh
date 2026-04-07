#!/usr/bin/env bash
# Deploy Oakton Alert pilot to AWS from repo root .env (Telnyx + optional keys).
# Usage (from repo root): ./deploy/deploy-pilot.sh
#
# Requires: aws CLI, sam CLI, valid AWS credentials (e.g. aws sso login --profile YOUR_PROFILE).
# If AWS_PROFILE is set, temporary AWS_ACCESS_KEY_* vars from .env are cleared so SSO is used.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Missing $ROOT/.env — copy .env.example and fill in values."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

# Legacy name support (match pilot-oakton-alert TELNYX_PUBLIC_KEY)
if [[ -z "${TELNYX_PUBLIC_KEY:-}" ]] && [[ -n "${TelnyxPublicKey:-}" ]]; then
  export TELNYX_PUBLIC_KEY="$TelnyxPublicKey"
fi

if [[ -z "${TELNYX_API_KEY:-}" ]] || [[ -z "${TELNYX_PHONE_NUMBER:-}" ]]; then
  echo "Set TELNYX_API_KEY and TELNYX_PHONE_NUMBER in .env"
  exit 1
fi

# Prefer named profile over possibly expired static keys in .env
if [[ -n "${AWS_PROFILE:-}" ]]; then
  unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN || true
fi

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "AWS credentials failed (ExpiredToken or not logged in)."
  echo "  Try: aws sso login --profile ${AWS_PROFILE:-default}"
  exit 1
fi

# SAM resolves --config-file relative to the template's directory; "deploy/samconfig-pilot.toml"
# becomes deploy/deploy/... and fails. Use absolute paths.
SOURCE_TEMPLATE="$ROOT/deploy/template-pilot.yaml"
# MUST deploy the built template: source template's CodeUri points at raw app source without pip deps.
BUILT_TEMPLATE="$ROOT/.aws-sam/build/template.yaml"
SAMCONFIG="$ROOT/deploy/samconfig-pilot.toml"

sam build -t "$SOURCE_TEMPLATE"

[[ -f "$BUILT_TEMPLATE" ]] || { echo "Missing $BUILT_TEMPLATE — sam build failed?"; exit 1; }

# SAM rejects empty Parameter=value pairs; omit optional params when blank.
PO=(
  "TelnyxApiKey=${TELNYX_API_KEY}"
  "TelnyxPhoneNumber=${TELNYX_PHONE_NUMBER}"
)
[[ -n "${TELNYX_MESSAGING_PROFILE_ID:-}" ]] && PO+=("TelnyxMessagingProfileId=${TELNYX_MESSAGING_PROFILE_ID}")
[[ -n "${TELNYX_PUBLIC_KEY:-}" ]] && PO+=("TelnyxPublicKey=${TELNYX_PUBLIC_KEY}")
[[ -n "${TRIGGER_API_KEY:-}" ]] && PO+=("TriggerApiKey=${TRIGGER_API_KEY}")

sam deploy -t "$BUILT_TEMPLATE" \
  --config-file "$SAMCONFIG" \
  --no-confirm-changeset \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --force-upload \
  --parameter-overrides "${PO[@]}"
