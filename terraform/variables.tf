# ============================================
# GENERAL
# ============================================
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ca-central-1"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "iot-lab"
}

# ============================================
# DATABASE
# ============================================
variable "db_username" {
  description = "Database username"
  type        = string
  default     = "iotadmin"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "iotplatform"
}

# ============================================
# RABBITMQ
# ============================================
variable "rabbitmq_username" {
  description = "RabbitMQ username"
  type        = string
  default     = "iotadmin"
}

variable "rabbitmq_password" {
  description = "RabbitMQ password"
  type        = string
  sensitive   = true
}

# ============================================
# APPLICATION
# ============================================
variable "jwt_secret" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
}

# ============================================
# FEATURE FLAGS
# ============================================
variable "enable_ecs" {
  description = "Enable ECS Fargate deployment"
  type        = bool
  default     = false
}

variable "enable_eks" {
  description = "Enable EKS cluster"
  type        = bool
  default     = false
}
