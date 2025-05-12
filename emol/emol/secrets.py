from functools import lru_cache
import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)

def get_aws_credentials():
    """Read AWS credentials from environment, fall back to file"""

    if "AWS_ACCESS_KEY_ID" in os.environ and "AWS_SECRET_ACCESS_KEY" in os.environ:
        return {
            "aws_access_key_id": os.environ["AWS_ACCESS_KEY_ID"],
            "aws_secret_access_key": os.environ["AWS_SECRET_ACCESS_KEY"],
        }
    elif os.path.exists("/usr/local/etc/emol_credentials.json"):
        with open("/usr/local/etc/emol_credentials.json", "r") as f:
            return json.load(f)    

def get_aws_session():
    """Get a boto3 session with AWS credentials"""

    credentials = get_aws_credentials()
    return boto3.session.Session(**credentials)

@lru_cache(maxsize=32)
def get_secret(name):
    credentials = get_aws_credentials()
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
