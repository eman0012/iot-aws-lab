# ============================================
# AWS CodeBuild for Database Migrations
# ============================================
# CodeBuild runs inside the VPC, allowing secure access to the
# private RDS instance without exposing it to the public internet.
#
# Why CodeBuild?
# - Runs inside VPC (secure access to private RDS)
# - Pay-per-use (~$0.005/min, typical migration ~$0.01)
# - Zero maintenance (AWS-managed)
# - Native IAM and Secrets Manager integration
# - Production-ready pattern used by enterprises
# ============================================

# ============================================
# IAM ROLE FOR CODEBUILD
# ============================================
resource "aws_iam_role" "codebuild" {
  name = "${var.project_name}-${var.environment}-codebuild-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codebuild.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-codebuild-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "codebuild" {
  name = "${var.project_name}-${var.environment}-codebuild-policy"
  role = aws_iam_role.codebuild.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # CloudWatch Logs for build output
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:/aws/codebuild/${var.project_name}-${var.environment}-*",
          "arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:/aws/codebuild/${var.project_name}-${var.environment}-*:*"
        ]
      },
      {
        # Secrets Manager access for DB credentials
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [var.secrets_arn]
      },
      {
        # VPC networking permissions
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeDhcpOptions",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeVpcs"
        ]
        Resource = "*"
      },
      {
        # Required for VPC interface creation
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterfacePermission"
        ]
        Resource = "arn:aws:ec2:${var.aws_region}:${var.account_id}:network-interface/*"
        Condition = {
          StringEquals = {
            "ec2:Subnet" = [
              for subnet_id in var.private_subnet_ids :
              "arn:aws:ec2:${var.aws_region}:${var.account_id}:subnet/${subnet_id}"
            ]
          }
        }
      },
      {
        # S3 access for migration artifacts
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:GetBucketLocation",
          "s3:ListBucket"
        ]
        Resource = [
          var.artifacts_bucket_arn,
          "${var.artifacts_bucket_arn}/*"
        ]
      }
    ]
  })
}

# ============================================
# SECURITY GROUP FOR CODEBUILD
# ============================================
resource "aws_security_group" "codebuild" {
  name_prefix = "${var.project_name}-${var.environment}-codebuild-"
  vpc_id      = var.vpc_id
  description = "Security group for CodeBuild database migrations"

  # Outbound to RDS
  egress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.rds_security_group_id]
    description     = "PostgreSQL to RDS"
  }

  # Outbound HTTPS for pip, AWS APIs
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS for package downloads and AWS APIs"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-codebuild-sg"
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow CodeBuild to access RDS (add ingress rule to RDS security group)
resource "aws_security_group_rule" "rds_from_codebuild" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = var.rds_security_group_id
  source_security_group_id = aws_security_group.codebuild.id
  description              = "PostgreSQL from CodeBuild migrations"
}

# ============================================
# CODEBUILD PROJECT - DATABASE MIGRATIONS
# ============================================
resource "aws_codebuild_project" "db_migrate" {
  name          = "${var.project_name}-${var.environment}-db-migrate"
  description   = "Run Alembic database migrations inside VPC"
  build_timeout = 10 # minutes
  service_role  = aws_iam_role.codebuild.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "DB_HOST"
      value = var.rds_endpoint
    }

    environment_variable {
      name  = "DB_NAME"
      value = var.db_name
    }

    environment_variable {
      name  = "SECRETS_ARN"
      value = var.secrets_arn
    }

    environment_variable {
      name  = "AWS_REGION"
      value = var.aws_region
    }
  }

  source {
    type      = "S3"
    location  = "${var.artifacts_bucket_name}/migrations.zip"
    buildspec = "buildspec.yml"
  }

  vpc_config {
    vpc_id             = var.vpc_id
    subnets            = var.private_subnet_ids
    security_group_ids = [aws_security_group.codebuild.id]
  }

  logs_config {
    cloudwatch_logs {
      group_name  = "/aws/codebuild/${var.project_name}-${var.environment}-db-migrate"
      stream_name = "migration-logs"
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-migrate"
    Environment = var.environment
    Purpose     = "Database migrations via Alembic"
  }
}

# ============================================
# CLOUDWATCH LOG GROUP
# ============================================
resource "aws_cloudwatch_log_group" "codebuild" {
  name              = "/aws/codebuild/${var.project_name}-${var.environment}-db-migrate"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-${var.environment}-codebuild-logs"
    Environment = var.environment
  }
}
