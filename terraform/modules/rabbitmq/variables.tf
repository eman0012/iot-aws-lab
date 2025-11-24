variable "project_name" { type = string }
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "rabbitmq_username" { type = string }
variable "rabbitmq_password" {
  type      = string
  sensitive = true
}
variable "allowed_sg_ids" { type = list(string) }
