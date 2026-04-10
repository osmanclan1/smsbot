"""
Shared DynamoDB client for pilot-v1 (opt-outs, campaigns, batches, send dedup).
When PILOT_DYNAMODB_TABLE is unset, callers should use storage.py in-memory fallback only.
"""

import os
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

_table_name: Optional[str] = None
_resource = None


def table_name() -> Optional[str]:
    global _table_name
    if _table_name is None:
        _table_name = (os.getenv("PILOT_DYNAMODB_TABLE") or "").strip() or None
    return _table_name


def table():
    global _resource
    if not table_name():
        raise RuntimeError("PILOT_DYNAMODB_TABLE is not set")
    if _resource is None:
        _resource = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1"))
    return _resource.Table(table_name())


def get_item(pk: str, sk: str) -> Optional[dict[str, Any]]:
    try:
        r = table().get_item(Key={"pk": pk, "sk": sk})
        return r.get("Item")
    except ClientError as e:
        print(f"DynamoDB get_item error: {e}")
        return None


def put_item(item: dict[str, Any]) -> bool:
    try:
        table().put_item(Item=item)
        return True
    except ClientError as e:
        print(f"DynamoDB put_item error: {e}")
        return False


def put_item_if_not_exists(item: dict[str, Any], pk_name: str = "pk") -> bool:
    """
    Conditional put for idempotency markers.
    Returns False when the item already exists.
    """
    try:
        table().put_item(
            Item=item,
            ConditionExpression=f"attribute_not_exists({pk_name})",
        )
        return True
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code == "ConditionalCheckFailedException":
            return False
        print(f"DynamoDB conditional put error: {e}")
        return False


def delete_item(pk: str, sk: str) -> bool:
    try:
        table().delete_item(Key={"pk": pk, "sk": sk})
        return True
    except ClientError as e:
        print(f"DynamoDB delete_item error: {e}")
        return False


