# ============================================
# CodeBuild Module Variables
# ============================================

variable "project_name" {
  description = "Project name prefix"
  type        = string
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for CodeBuild"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for CodeBuild"
  type        = list(string)
}

variable "rds_endpoint" {
  description = "RDS endpoint (host:port)"
  type        = string
}

variable "rds_security_group_id" {
  description = "RDS security group ID for egress rules"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "secrets_arn" {
  description = "Secrets Manager ARN for database credentials"
  type        = string
}

variable "github_repo_url" {
  description = "GitHub repository URL"
  type        = string
  default     = "https://github.com/your-username/iot-aws-lab.git"
}
