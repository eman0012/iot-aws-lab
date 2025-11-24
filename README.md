# IoT Platform - AWS Implementation

Complete AWS serverless IoT platform with Lambda functions, RDS PostgreSQL, Amazon MQ RabbitMQ, and API Gateway.

## Architecture

```
┌─────────────┐
│   Devices   │
└──────┬──────┘
       │
       v
┌─────────────────────────────────────────────┐
│          API Gateway HTTP API v2             │
└──────┬──────────────────────────────────────┘
       │
       v
┌─────────────────────────────────────────────┐
│     Lambda Functions (Python 3.10)          │
│  - users      - devices    - telemetry      │
│  - conditions - alertlogs  - admin          │
└──┬───────────────────────┬──────────────────┘
   │                       │
   v                       v
┌──────────┐         ┌──────────┐
│ RDS PG   │         │ RabbitMQ │
│ (15.4)   │         │ (3.11)   │
└──────────┘         └──────────┘
```

## Project Structure

```
iot-aws-lab/
├── terraform/              # Infrastructure as Code
│   ├── modules/           # Terraform modules (11 total)
│   │   ├── vpc/
│   │   ├── rds/
│   │   ├── rabbitmq/
│   │   ├── lambda/
│   │   ├── s3/
│   │   └── ...
│   ├── main.tf
│   └── variables.tf
├── lambda/                # Lambda functions
│   ├── shared/           # Shared services layer
│   ├── users/
│   ├── devices/
│   ├── telemetry/
│   ├── conditions/
│   ├── alertlogs/
│   ├── admin/
│   └── build_all.sh
├── go-cli/               # CLI testing tool
│   ├── cmd/
│   └── go.mod
├── docker/               # Docker configurations
├── .github/workflows/    # CI/CD pipelines
└── scripts/              # Utility scripts
```

## Quick Start

### Prerequisites

- AWS CLI configured (Account: 537124935206)
- Terraform >= 1.0
- Go >= 1.21
- Python >= 3.10
- Docker (optional)

### 1. Generate Secrets

```bash
cd terraform

DB_PASS=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
MQ_PASS=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
JWT_SECRET=$(openssl rand -base64 32)

cat > terraform.tfvars << EOF
aws_region        = "ca-central-1"
environment       = "dev"
project_name      = "iot-lab"
db_username       = "iotadmin"
db_password       = "${DB_PASS}"
db_name           = "iotplatform"
rabbitmq_username = "iotadmin"
rabbitmq_password = "${MQ_PASS}"
jwt_secret        = "${JWT_SECRET}"
enable_ecs        = false
enable_eks        = false
EOF
```

### 2. Deploy Infrastructure

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply infrastructure
terraform apply tfplan

# Get outputs
terraform output
```

### 3. Build and Deploy Lambda Functions

```bash
cd lambda

# Build all functions
chmod +x build_all.sh
./build_all.sh

# Deploy manually or use GitHub Actions
# The build creates:
# - build/shared-layer.zip
# - build/users.zip, devices.zip, telemetry.zip, etc.
```

### 4. Initialize Database

```bash
# Connect to RDS (use endpoint from terraform output)
psql -h <rds-endpoint> -U iotadmin -d iotplatform -f scripts/init-db.sql
```

### 5. Test with Go CLI

```bash
cd go-cli

# Build CLI
go build -o iot-cli cmd/main.go

# Set API URL (from terraform output)
export IOT_API_URL="https://xxx.execute-api.ca-central-1.amazonaws.com"

# Test health
./iot-cli health

# Register user
./iot-cli login -e user@example.com -p password123
```

## API Endpoints

### User Management
- `POST /api/user` - Register new user
- `POST /api/user/login` - User login
- `GET /api/user` - Get user profile
- `PUT /api/user` - Update user profile
- `PATCH /api/user/password` - Change password
- `DELETE /api/user` - Delete account

### Device Management
- `POST /api/device` - Register device
- `GET /api/devices` - List user devices
- `PUT /api/device` - Update device
- `DELETE /api/device` - Delete device

### Telemetry
- `POST /api/telemetry` - Submit telemetry data
- `GET /api/telemetry` - Get telemetry history
- `DELETE /api/telemetry` - Delete telemetry record

### Conditions (Alert Rules)
- `POST /api/conditions` - Create condition
- `GET /api/conditions` - List conditions
- `PUT /api/conditions` - Update condition
- `DELETE /api/conditions` - Delete condition

### Alert Logs
- `GET /api/alertlogs` - Get alert logs
- `DELETE /api/alertlogs` - Delete alert log

### Admin (Admin only)
- `GET /api/manage/users` - List all users
- `PUT /api/manage/change-user-type` - Change user type
- `POST /api/manage/transfer-device` - Transfer device ownership
- `GET /api/manage/images` - Get S3 presigned URL

## Local Development

### Using Docker Compose

```bash
# Start local PostgreSQL and RabbitMQ
docker-compose up -d

# Initialize database
psql -h localhost -U iotadmin -d iotplatform -f scripts/init-db.sql

# Test locally (requires local API server or use Lambda SAM)
```

## CI/CD

GitHub Actions workflows are configured for:

1. **Terraform** (`.github/workflows/terraform.yml`)
   - Format check
   - Plan on PR
   - Apply on main branch push

2. **Lambda Deployment** (`.github/workflows/lambda-deploy.yml`)
   - Build Lambda packages
   - Deploy layer and functions

3. **Go CLI Build** (`.github/workflows/go-build.yml`)
   - Build for Linux, macOS, Windows
   - Upload artifacts

### Required GitHub Secrets

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DB_PASSWORD`
- `RABBITMQ_PASSWORD`
- `JWT_SECRET`

## Infrastructure Details

### VPC
- CIDR: 10.0.0.0/16
- 2 AZs: ca-central-1a, ca-central-1b
- Public subnets: 10.0.1.0/24, 10.0.2.0/24
- Private subnets: 10.0.10.0/24, 10.0.11.0/24
- NAT Gateway for private subnet internet access
- VPC Endpoints: S3, Secrets Manager, ECR

### RDS PostgreSQL
- Engine: PostgreSQL 15.4
- Instance: db.t3.micro
- Storage: 20GB gp3 (auto-scaling to 100GB)
- Encrypted at rest
- Performance Insights enabled (7-day retention)
- Automated backups: 7 days

### Amazon MQ (RabbitMQ)
- Engine: RabbitMQ 3.11.20
- Instance: mq.t3.micro
- Single-instance deployment (dev)
- Auto minor version upgrades
- General logging enabled

### Lambda Functions
- Runtime: Python 3.10
- Memory: 512 MB
- Timeout: 30 seconds
- VPC-attached (private subnets)
- Shared layer with dependencies

### API Gateway
- Type: HTTP API v2
- CORS enabled
- CloudWatch logging
- 26 routes total

### S3
- Telemetry image storage
- Versioning enabled
- Encryption: AES256
- Public access blocked

### Secrets Manager
- Centralized secret storage
- Automatic rotation supported
- Used by Lambda for DB/RabbitMQ credentials

### CloudWatch
- Dashboard with Lambda metrics
- Log groups for all functions
- API Gateway access logs

## Cost Estimates

Development environment (dev):
- RDS db.t3.micro: ~$15/month
- Amazon MQ t3.micro: ~$40/month
- Lambda: Pay per request (~$0-5/month for low traffic)
- API Gateway: $1 per million requests
- S3: Negligible for small datasets
- NAT Gateway: ~$32/month

**Total: ~$90-100/month**

## Security Features

- All resources in VPC private subnets
- Security groups with least-privilege access
- JWT authentication with bcrypt password hashing
- Secrets stored in AWS Secrets Manager
- Encrypted RDS and S3 storage
- IAM roles with minimal permissions
- VPC endpoints to avoid internet routing

## Monitoring

- CloudWatch dashboard for Lambda metrics
- RDS Performance Insights
- API Gateway access logs
- Lambda function logs
- CloudWatch alarms (can be configured)

## Migration Notes

This project is a complete AWS implementation matching the Azure IoT platform documented in `AZURE_PROJECT_REFERENCE.md`:

- Azure Functions → AWS Lambda
- Azure Cosmos DB → RDS PostgreSQL
- Azure Service Bus → Amazon MQ (RabbitMQ)
- Azure API Management → API Gateway
- Azure Blob Storage → S3
- Azure Key Vault → AWS Secrets Manager

All API endpoints, request/response structures, and business logic remain identical to ensure compatibility.

## Documentation

- `CLAUDE.md` - Development guide and commands
- `AZURE_PROJECT_REFERENCE.md` - Original Azure implementation reference
- `MIGRATION_PROGRESS.md` - Migration status and progress
- `go-cli/README.md` - CLI tool documentation
- `lambda/README.md` - Lambda function details (if needed)

## Support

For issues or questions:
1. Check existing documentation
2. Review CloudWatch logs
3. Verify AWS credentials and permissions
4. Ensure all required secrets are configured

## License

Educational project for cloud migration practice.
