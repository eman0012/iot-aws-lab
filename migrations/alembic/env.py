"""
Alembic Environment Configuration

This file configures how Alembic connects to the database and runs migrations.
Supports both local development and CI/CD environments.
"""
import os
import json
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# Alembic Config object
config = context.config

# Setup logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_database_url():
    """
    Get database URL from environment or AWS Secrets Manager.

    Priority:
    1. DATABASE_URL environment variable (for local dev)
    2. AWS Secrets Manager (for CI/CD and production)
    """
    # Check for direct DATABASE_URL first (local development)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return database_url

    # Check for individual components (CI/CD with GitHub secrets)
    db_host = os.environ.get('DB_HOST')
    db_name = os.environ.get('DB_NAME')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')

    if all([db_host, db_name, db_user, db_password]):
        return f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"

    # Try AWS Secrets Manager (production)
    secrets_arn = os.environ.get('SECRETS_ARN')
    if secrets_arn:
        try:
            import boto3
            region = os.environ.get('AWS_REGION', 'ca-central-1')
            client = boto3.client('secretsmanager', region_name=region)
            response = client.get_secret_value(SecretId=secrets_arn)
            secrets = json.loads(response['SecretString'])

            db_host = os.environ.get('DB_HOST')  # Still need host from env
            return f"postgresql://{secrets['db_username']}:{secrets['db_password']}@{db_host}:5432/{secrets['db_name']}"
        except Exception as e:
            raise RuntimeError(f"Failed to get secrets from AWS: {e}")

    raise RuntimeError(
        "Database configuration not found. Set DATABASE_URL or "
        "DB_HOST/DB_NAME/DB_USER/DB_PASSWORD environment variables."
    )


def run_migrations_offline():
    """
    Run migrations in 'offline' mode.

    This generates SQL scripts without connecting to the database.
    Useful for review or manual execution.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations in 'online' mode.

    This connects to the database and executes migrations directly.
    Used in CI/CD and production deployments.
    """
    # Create engine with SSL required for RDS
    url = get_database_url()

    # Add SSL mode for RDS connections
    connect_args = {}
    if 'rds.amazonaws.com' in url:
        connect_args['sslmode'] = 'require'

    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
        connect_args=connect_args
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None
        )

        with context.begin_transaction():
            context.run_migrations()


# Run appropriate migration mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
