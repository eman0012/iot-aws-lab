variable "project_name" { type = string }
variable "environment" { type = string }
variable "lambda_function_names" { type = list(string) }
variable "rds_instance_id" { type = string }
variable "rabbitmq_broker_id" { type = string }
variable "s3_bucket_name" { type = string }
