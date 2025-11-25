# ============================================
# SECURITY GROUP
# ============================================
resource "aws_security_group" "rabbitmq" {
  name_prefix = "${var.project_name}-rabbitmq-"
  vpc_id      = var.vpc_id

  # AMQPS
  ingress {
    from_port       = 5671
    to_port         = 5671
    protocol        = "tcp"
    security_groups = var.allowed_sg_ids
    description     = "AMQPS from allowed security groups"
  }

  # HTTPS Management
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = var.allowed_sg_ids
    description     = "HTTPS management"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-${var.environment}-rabbitmq-sg" }
  lifecycle { create_before_destroy = true }
}

# ============================================
# AMAZON MQ BROKER
# ============================================
resource "aws_mq_broker" "rabbitmq" {
  broker_name        = "${var.project_name}-${var.environment}-rabbitmq"
  engine_type        = "RabbitMQ"
  engine_version     = "3.13"
  host_instance_type = "mq.t3.micro"
  deployment_mode    = "SINGLE_INSTANCE"

  user {
    username = var.rabbitmq_username
    password = var.rabbitmq_password
  }

  subnet_ids          = [var.private_subnet_ids[0]]
  security_groups     = [aws_security_group.rabbitmq.id]
  publicly_accessible = false

  auto_minor_version_upgrade = true

  logs {
    general = true
  }

  maintenance_window_start_time {
    day_of_week = "SUNDAY"
    time_of_day = "03:00"
    time_zone   = "UTC"
  }

  tags = { Name = "${var.project_name}-${var.environment}-rabbitmq" }
}
