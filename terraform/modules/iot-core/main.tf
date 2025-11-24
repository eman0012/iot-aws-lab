# IoT Core Policy for devices
resource "aws_iot_policy" "device_policy" {
  name = "${var.project_name}-${var.environment}-device-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iot:Connect",
          "iot:Publish",
          "iot:Subscribe",
          "iot:Receive"
        ]
        Resource = "*"
      }
    ]
  })
}

# IoT Topic Rule (placeholder - will forward telemetry to Lambda)
resource "aws_iot_topic_rule" "telemetry" {
  name        = "${replace(var.project_name, "-", "_")}_${var.environment}_telemetry"
  enabled     = true
  sql         = "SELECT * FROM 'telemetry/#'"
  sql_version = "2016-03-23"

  # Lambda action would be added here after Lambda module is created
  error_action {
    cloudwatch_logs {
      log_group_name = aws_cloudwatch_log_group.iot.name
      role_arn       = aws_iam_role.iot.arn
    }
  }
}

resource "aws_cloudwatch_log_group" "iot" {
  name              = "/aws/iot/${var.project_name}-${var.environment}"
  retention_in_days = 7
}

resource "aws_iam_role" "iot" {
  name = "${var.project_name}-${var.environment}-iot-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "iot.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "iot_cloudwatch" {
  name = "cloudwatch-logs"
  role = aws_iam_role.iot.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.iot.arn}:*"
      }
    ]
  })
}
