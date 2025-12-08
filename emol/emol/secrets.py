import json
import logging
import os
from functools import lru_cache

import boto3

logger = logging.getLogger(__name__)


def get_aws_credentials():
    """Read AWS credentials from environment, fall back to file"""

    # For development environment
    if os.environ.get("EMOL_DEV"):
        return {
            "aws_access_key_id": "test",
            "aws_secret_access_key": "test",
            "region_name": os.environ.get("AWS_DEFAULT_REGION", "ca-central-1"),
        }

    if "AWS_ACCESS_KEY_ID" in os.environ and "AWS_SECRET_ACCESS_KEY" in os.environ:
        return {
            "aws_access_key_id": os.environ["AWS_ACCESS_KEY_ID"],
            "aws_secret_access_key": os.environ["AWS_SECRET_ACCESS_KEY"],
        }
    elif os.path.exists("/opt/emol/emol_credentials.json"):
        with open("/opt/emol/emol_credentials.json", "r") as f:
            return json.load(f)

    logger.error("No AWS credentials found")
    return None


def get_aws_session():
    """Get a boto3 session with AWS credentials"""
    credentials = get_aws_credentials()
    if not credentials:
        raise Exception("No AWS credentials available")
    return boto3.session.Session(**credentials)


@lru_cache(maxsize=32)
def get_secret(name):
    """Get a secret from SSM Parameter Store"""
    if os.environ.get("EMOL_DEV"):
        # Development environment defaults
        dev_secrets = {
            "/emol/django_settings_module": "emol.settings.dev",
            "/emol/db_host": "db",
            "/emol/db_name": "emol",
            "/emol/db_user": "emol_db_user",
            "/emol/db_password": "emol_db_password",
            # OAuth credentials should be set via SSM, even in dev
        }
        return dev_secrets.get(name)

    credentials = get_aws_credentials()
    if not credentials:
        raise Exception("No AWS credentials available")

    ssm_kwargs = {}
    if os.environ.get("SSM_ENDPOINT_URL"):
        ssm_kwargs["endpoint_url"] = os.environ.get("SSM_ENDPOINT_URL")

    session = get_aws_session()
    ssm = session.client("ssm", **ssm_kwargs)

    try:
        response = ssm.get_parameter(Name=name, WithDecryption=True)
        return response["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound as exc:
        logger.error(f"Parameter '{name}' not found: {exc}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving parameter '{name}': {str(e)}")
        return None
