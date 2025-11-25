resource "aws_secretsmanager_secret" "main" {
  name                    = "${var.project_name}-${var.environment}-secrets"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-secrets"
  }
}

resource "aws_secretsmanager_secret_version" "main" {
  secret_id = aws_secretsmanager_secret.main.id

  secret_string = jsonencode({
    db_username       = var.db_username
    db_password       = var.db_password
    db_name           = var.db_name
    rabbitmq_username = var.rabbitmq_username
    rabbitmq_password = var.rabbitmq_password
    jwt_secret        = var.jwt_secret
    jwt_algorithm     = "HS256"
  })
}
