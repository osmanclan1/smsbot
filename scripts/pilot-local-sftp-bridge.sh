#!/usr/bin/env bash
# Push a local "SFTP drop" folder to the pilot v1 S3 prefix so PilotIngestFunction runs
# (same as aws s3 cp) — see docs/PILOT_E2E_SFTP.md.
#
# Usage (from repo root):
#   ./scripts/pilot-local-sftp-bridge.sh              # one-shot sync
#   ./scripts/pilot-local-sftp-bridge.sh --watch    # sync when files change (needs fswatch or inotifywait)
#   ./scripts/pilot-local-sftp-bridge.sh --delete   # sync and remove S3 keys missing locally (careful on shared buckets)
#
# Env (optional; repo root .env is sourced if present):
#   PILOT_INBOUND_BUCKET   S3 bucket name (if unset, resolved from CloudFormation output PilotInboundBucketName)
#   PILOT_STACK_NAME       default: smsbot-pilot-v1-stack
#   PILOT_SFTP_LOCAL_DIR   default: ~/pilot-sftp-incoming
#   AWS_PROFILE / AWS_REGION — standard AWS CLI
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

WATCH=false
DELETE_FLAG=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --watch) WATCH=true; shift ;;
    --delete) DELETE_FLAG=(--delete); shift ;;
    -h|--help)
      grep '^#' "$0" | grep -v '^#!' | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

if [[ -n "${AWS_PROFILE:-}" ]]; then
  unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN || true
fi

LOCAL_DIR="${PILOT_SFTP_LOCAL_DIR:-$HOME/pilot-sftp-incoming}"
mkdir -p "$LOCAL_DIR"

STACK="${PILOT_STACK_NAME:-smsbot-pilot-v1-stack}"
BUCKET="${PILOT_INBOUND_BUCKET:-}"

if [[ -z "$BUCKET" ]]; then
  if ! BUCKET="$(aws cloudformation describe-stacks \
      --stack-name "$STACK" \
      --query "Stacks[0].Outputs[?OutputKey=='PilotInboundBucketName'].OutputValue | [0]" \
      --output text 2>/dev/null)"; then
    echo "Could not resolve bucket from stack $STACK. Set PILOT_INBOUND_BUCKET in .env or deploy the stack." >&2
    exit 1
  fi
  if [[ -z "$BUCKET" || "$BUCKET" == "None" ]]; then
    echo "Stack $STACK has no PilotInboundBucketName output. Set PILOT_INBOUND_BUCKET in .env." >&2
    exit 1
  fi
fi

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "AWS credentials failed. Try: aws sso login --profile \${AWS_PROFILE:-default}" >&2
  exit 1
fi

sync_once() {
  # Keep object keys as incoming/<filename> — flat folder root matches Lambda prefix incoming/
  # macOS ships Bash 3.2: optional --delete must branch (empty arrays + `set -u` error).
  if ((${#DELETE_FLAG[@]})); then
    aws s3 sync "$LOCAL_DIR" "s3://${BUCKET}/incoming/" "${DELETE_FLAG[@]}" \
      --exclude ".DS_Store" \
      --exclude "._*" \
      --exclude "*.swp" \
      --exclude ".git/*" \
      --exclude ".Trash/*"
  else
    aws s3 sync "$LOCAL_DIR" "s3://${BUCKET}/incoming/" \
      --exclude ".DS_Store" \
      --exclude "._*" \
      --exclude "*.swp" \
      --exclude ".git/*" \
      --exclude ".Trash/*"
  fi
  echo "Synced $(date -u +"%Y-%m-%dT%H:%M:%SZ") → s3://${BUCKET}/incoming/"
}

if [[ "$WATCH" == false ]]; then
  sync_once
  exit 0
fi

if command -v fswatch >/dev/null 2>&1; then
  echo "Watching $LOCAL_DIR (fswatch); Ctrl+C to stop."
  sync_once
  # Debounce bursts (SFTP writes often touch temp files then rename)
  fswatch -o "$LOCAL_DIR" | while read -r _; do
    sleep 2
    sync_once
  done
elif command -v inotifywait >/dev/null 2>&1; then
  echo "Watching $LOCAL_DIR (inotifywait); Ctrl+C to stop."
  sync_once
  while true; do
    inotifywait -r -e close_write,create,moved_to --format '%w%f' "$LOCAL_DIR" 2>/dev/null || true
    sleep 2
    sync_once
  done
else
  echo "Install fswatch (macOS: brew install fswatch) or inotify-tools (Linux) for --watch." >&2
  exit 1
fi
