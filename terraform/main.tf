# ============================================
# DATA SOURCES
# ============================================
data "aws_caller_identity" "current" {}

# ============================================
# P0: CORE INFRASTRUCTURE
# ============================================

module "vpc" {
  source       = "./modules/vpc"
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
}

module "secrets" {
  source            = "./modules/secrets"
  project_name      = var.project_name
  environment       = var.environment
  db_username       = var.db_username
  db_password       = var.db_password
  db_name           = var.db_name
  rabbitmq_username = var.rabbitmq_username
  rabbitmq_password = var.rabbitmq_password
  jwt_secret        = var.jwt_secret
}

module "s3" {
  source       = "./modules/s3"
  project_name = var.project_name
  environment  = var.environment
}

module "rds" {
  source             = "./modules/rds"
  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  db_username        = var.db_username
  db_password        = var.db_password
  db_name            = var.db_name
  allowed_sg_ids     = [module.lambda.security_group_id]
}

module "rabbitmq" {
  source             = "./modules/rabbitmq"
  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  rabbitmq_username  = var.rabbitmq_username
  rabbitmq_password  = var.rabbitmq_password
  allowed_sg_ids     = [module.lambda.security_group_id]
}

module "lambda" {
  source             = "./modules/lambda"
  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  secrets_arn        = module.secrets.secret_arn
  s3_bucket_name     = module.s3.bucket_name
  s3_bucket_arn      = module.s3.bucket_arn
  rds_endpoint       = module.rds.endpoint
  rds_db_name        = var.db_name
  rabbitmq_endpoint  = module.rabbitmq.broker_endpoint
}

module "monitoring" {
  source                = "./modules/monitoring"
  project_name          = var.project_name
  environment           = var.environment
  lambda_function_names = module.lambda.function_names
  rds_instance_id       = module.rds.instance_id
  rabbitmq_broker_id    = module.rabbitmq.broker_id
  s3_bucket_name        = module.s3.bucket_name
}

module "iot_core" {
  source       = "./modules/iot-core"
  project_name = var.project_name
  environment  = var.environment
}

# ============================================
# DATABASE MIGRATIONS (CodeBuild in VPC)
# ============================================
module "codebuild" {
  source                = "./modules/codebuild"
  project_name          = var.project_name
  environment           = var.environment
  aws_region            = var.aws_region
  account_id            = data.aws_caller_identity.current.account_id
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  rds_endpoint          = module.rds.address
  rds_security_group_id = module.rds.security_group_id
  db_name               = var.db_name
  secrets_arn           = module.secrets.secret_arn
  github_repo_url       = var.github_repo_url
}

# ============================================
# P1: ECS FARGATE (Optional)
# ============================================
module "ecs" {
  count = var.enable_ecs ? 1 : 0

  source             = "./modules/ecs"
  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids
  secrets_arn        = module.secrets.secret_arn
}

# ============================================
# P2: EKS (Optional)
# ============================================
module "eks" {
  count = var.enable_eks ? 1 : 0

  source             = "./modules/eks"
  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
}
