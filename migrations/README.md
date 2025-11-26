# Database Migrations

This directory contains Alembic database migrations for the IoT Platform PostgreSQL database.

## Architecture Decision

### Why Alembic + CodeBuild?

We use **Alembic** for database migrations running inside **AWS CodeBuild** in the VPC.

| Requirement | Solution |
|-------------|----------|
| Version-controlled schema | Alembic migrations in Git |
| Private RDS access | CodeBuild runs inside VPC |
| Zero infrastructure maintenance | CodeBuild is AWS-managed |
| Cost-effective | Pay-per-use (~$0.01/migration) |
| CI/CD integration | GitHub Actions triggers CodeBuild |
| Production-ready | Enterprise pattern, IAM-secured |

### Alternatives Considered

| Option | Why Not Chosen |
|--------|---------------|
| **Flyway** | Alembic aligns better with Python stack; same concepts |
| **Public RDS** | Security risk in production; not best practice |
| **Bastion host** | $8+/month ongoing cost; server to maintain |
| **Lambda migration** | Would duplicate SQL in two places |
| **RDS Query Editor** | Manual, no version control, not repeatable |

## Directory Structure

```
migrations/
├── alembic.ini           # Alembic configuration
├── buildspec.yml         # CodeBuild build specification
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── alembic/
    ├── env.py            # Database connection configuration
    ├── script.py.mako    # Migration template
    └── versions/         # Migration files
        └── 20241125_0001_001_initial_schema.py
```

## How It Works

### CI/CD Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  GitHub Push    │────▶│  Terraform      │────▶│  CodeBuild      │
│  (main branch)  │     │  (infrastructure)│     │  (in VPC)       │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  RDS PostgreSQL │
                                                │  (private subnet)│
                                                └─────────────────┘
```

1. Developer pushes to `main` branch
2. GitHub Actions runs Terraform (infrastructure)
3. GitHub Actions triggers CodeBuild
4. CodeBuild runs inside VPC, connects to private RDS
5. Alembic applies pending migrations

### Security

- RDS is in a **private subnet** (no public access)
- CodeBuild runs **inside the VPC** with security group rules
- Database credentials stored in **AWS Secrets Manager**
- CodeBuild IAM role has **least-privilege access**

## Local Development

### Prerequisites

```bash
# Install dependencies
cd migrations
pip install -r requirements.txt

# Set environment variables (for local testing against a local DB)
export DATABASE_URL="postgresql://user:pass@localhost:5432/iotplatform"
```

### Common Commands

```bash
# Check current migration version
alembic current

# View migration history
alembic history

# Create a new migration
alembic revision -m "add_new_table"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 001

# Generate SQL without applying (offline mode)
alembic upgrade head --sql
```

### Creating a New Migration

1. Create the migration file:
   ```bash
   alembic revision -m "description_of_change"
   ```

2. Edit the generated file in `alembic/versions/`:
   ```python
   def upgrade() -> None:
       op.create_table('new_table', ...)

   def downgrade() -> None:
       op.drop_table('new_table')
   ```

3. Commit and push - CI/CD will apply it automatically

## Manual Deployment

### Via AWS CLI (trigger CodeBuild directly)

```bash
# Start migration build
aws codebuild start-build \
  --project-name iot-lab-dev-db-migrate \
  --source-version main

# Watch build logs
aws logs tail /aws/codebuild/iot-lab-dev-db-migrate --follow
```

### Via GitHub Actions

Push to `main` branch or manually trigger the workflow:

```bash
gh workflow run terraform.yml
```

## Troubleshooting

### Migration Failed

1. Check CodeBuild logs:
   ```bash
   aws logs tail /aws/codebuild/iot-lab-dev-db-migrate --since 1h
   ```

2. Check current database state:
   ```bash
   # Via Lambda or bastion (if available)
   psql -h $RDS_ENDPOINT -U iotadmin -d iotplatform -c "SELECT * FROM alembic_version"
   ```

### Rollback a Failed Migration

1. Fix the migration file or create a new downgrade migration
2. Manually invoke CodeBuild with downgrade command (requires modification to buildspec)

### Connection Issues

- Verify CodeBuild security group allows egress to RDS (port 5432)
- Verify RDS security group allows ingress from CodeBuild
- Check VPC subnet routing and NAT gateway for package downloads

## Schema Overview

The initial migration (`001`) creates these tables matching the Azure Cosmos DB structure:

| Table | Purpose | Azure Equivalent |
|-------|---------|------------------|
| `users` | User accounts | `Users` collection |
| `devices` | IoT devices | `Users.Devices[]` embedded array |
| `telemetry` | Sensor readings | `Devices[].telemetryData[]` |
| `conditions` | Alert rules | `Conditions` collection |
| `alert_logs` | Triggered alerts | `AlertLogs` collection |
| `logs` | System logs | `Logs` collection |
| `image_analysis` | Rekognition results | (new for AWS) |

## Cost Estimate

| Component | Cost |
|-----------|------|
| CodeBuild | ~$0.005/min (BUILD_GENERAL1_SMALL) |
| Typical migration | ~2 min = $0.01 |
| Monthly (10 deploys) | ~$0.10 |
