import base64
import json
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

ENV = os.environ.get("ENV", "Staging")


def _get_secret_json(secret_arn: str, region_name: str = "us-east-1") -> Dict[str, Any]:
    """Fetch and parse a JSON secret from AWS Secrets Manager."""
    session = boto3.Session(region_name=region_name)
    client = session.client("secretsmanager")

    try:
        response = client.get_secret_value(SecretId=secret_arn)
    except ClientError as exc:
        raise RuntimeError(
            f"Failed to fetch secret from AWS Secrets Manager: secret_arn={secret_arn}"
        ) from exc

    secret_string = _extract_secret_string(response, secret_arn)
    try:
        return json.loads(secret_string)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Secret value is not valid JSON: secret_arn={secret_arn}"
        ) from exc


def _extract_secret_string(response: Dict[str, Any], secret_arn: str) -> str:
    if response.get("SecretBinary"):
        decoded = base64.b64decode(response["SecretBinary"])
        return decoded.decode("utf-8")
    secret_string = response.get("SecretString")
    if not secret_string:
        raise ValueError(
            f"Secret did not contain SecretString or SecretBinary: secret_arn={secret_arn}"
        )
    return secret_string


def get_secret(
    secret_arn: str,
    region_name: str = "us-east-1",
    host=os.getenv("MYSQL_HOST"),
    db_name=os.getenv("MYSQL_DB_NAME"),
    port=os.getenv("MYSQL_PORT"),
) -> Dict[str, Any]:
    """
    Load DB credentials from AWS Secrets Manager and host from SSM Parameter Store.

    Example:
        # from reach_commons.reach_aws import get_secret
        # config = get_secret(
        # os.environ[ "RDS_SECRET_ARN"],
        #)
    """

    if not secret_arn:
        raise ValueError(f"RDS secret ARN is not configured")
    if not host:
        raise ValueError(f"RDS host is not configured")

    secrets_data = None

    if secrets_data is None:
        secrets_data = _get_secret_json(secret_arn, region_name)

    if not isinstance(secrets_data, dict):
        raise ValueError(
            f"Secret payload must be a JSON object: secret_arn={secret_arn}"
        )

    secrets_data["host"] = host
    secrets_data["dbname"] = db_name

    if port is None:
        secrets_data["port"] = 3306

    missing = [
        key
        for key in ("host", "username", "password", "dbname")
        if key not in secrets_data
    ]
    if missing:
        raise ValueError(
            "Secret is missing required fields: "
            f"missing={missing}, secret_arn={secret_arn}"
        )

    return secrets_data
