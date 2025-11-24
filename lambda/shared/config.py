import os
import json
import boto3
from functools import lru_cache

@lru_cache(maxsize=1)
def get_secrets():
    """Load secrets from AWS Secrets Manager with caching"""
    secrets_arn = os.environ.get('SECRETS_ARN')
    if not secrets_arn:
        raise EnvironmentError("SECRETS_ARN environment variable not set")

    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secrets_arn)
    return json.loads(response['SecretString'])

def get_config():
    """Get application configuration combining env vars and secrets"""
    secrets = get_secrets()

    return {
        # Database
        "DB_HOST": os.environ.get("DB_HOST", "").split(":")[0],  # Remove port
        "DB_PORT": 5432,
        "DB_NAME": os.environ.get("DB_NAME", secrets.get("db_name", "iotaccessibility")),
        "DB_USERNAME": secrets.get("db_username"),
        "DB_PASSWORD": secrets.get("db_password"),

        # RabbitMQ
        "RABBITMQ_HOST": os.environ.get("RABBITMQ_HOST", "").replace("amqps://", "").split(":")[0],
        "RABBITMQ_PORT": 5671,
        "RABBITMQ_USERNAME": secrets.get("rabbitmq_username"),
        "RABBITMQ_PASSWORD": secrets.get("rabbitmq_password"),

        # Application
        "JWT_SECRET": secrets.get("jwt_secret"),
        "JWT_ALGORITHM": secrets.get("jwt_algorithm", "HS256"),
        "JWT_EXPIRY_HOURS": 24,

        # AWS Resources
        "S3_BUCKET": os.environ.get("S3_BUCKET"),
        "QUEUE_NAME": os.environ.get("QUEUE_NAME", "telemetry-queue"),
        "ENVIRONMENT": os.environ.get("ENVIRONMENT", "dev"),
    }
