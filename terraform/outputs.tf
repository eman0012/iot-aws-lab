# ============================================
# API ENDPOINTS
# ============================================
output "api_gateway_url" {
  description = "API Gateway endpoint"
  value       = module.lambda.api_gateway_url
}

# ============================================
# INFRASTRUCTURE
# ============================================
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "rabbitmq_endpoint" {
  description = "RabbitMQ broker endpoint"
  value       = module.rabbitmq.broker_endpoint
  sensitive   = true
}

output "rabbitmq_console" {
  description = "RabbitMQ management console URL"
  value       = module.rabbitmq.console_url
}

output "s3_bucket" {
  value = module.s3.bucket_name
}

# ============================================
# MONITORING
# ============================================
output "cloudwatch_dashboard_url" {
  value = module.monitoring.dashboard_url
}

# ============================================
# SECRETS
# ============================================
output "secrets_arn" {
  value     = module.secrets.secret_arn
  sensitive = true
}

# ============================================
# CONTAINER SERVICES (when enabled)
# ============================================
output "ecs_cluster_name" {
  value = var.enable_ecs ? module.ecs[0].cluster_name : "ECS not enabled"
}

output "eks_cluster_name" {
  value = var.enable_eks ? module.eks[0].cluster_name : "EKS not enabled"
}
