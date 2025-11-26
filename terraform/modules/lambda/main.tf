# Lambda Security Group
resource "aws_security_group" "lambda" {
  name_prefix = "${var.project_name}-lambda-"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_exec" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom" {
  name = "lambda-custom-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.secrets_arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${var.s3_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = var.s3_bucket_arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda Layer for shared code
resource "aws_lambda_layer_version" "shared" {
  filename            = "${path.module}/../../../lambda/build/shared-layer.zip"
  layer_name          = "${var.project_name}-${var.environment}-shared"
  compatible_runtimes = ["python3.10"]
  source_code_hash    = fileexists("${path.module}/../../../lambda/build/shared-layer.zip") ? filebase64sha256("${path.module}/../../../lambda/build/shared-layer.zip") : ""

  lifecycle {
    ignore_changes = [source_code_hash]
  }
}

# Lambda Functions
locals {
  # API-triggered functions
  lambda_functions = ["users", "devices", "telemetry", "conditions", "alertlogs", "admin"]
  # Background consumer functions (triggered by CloudWatch Events)
  consumer_functions = ["consumers"]
}

resource "aws_lambda_function" "functions" {
  for_each = toset(local.lambda_functions)

  filename         = "${path.module}/../../../lambda/build/${each.key}.zip"
  function_name    = "${var.project_name}-${var.environment}-${each.key}"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.main"
  source_code_hash = fileexists("${path.module}/../../../lambda/build/${each.key}.zip") ? filebase64sha256("${path.module}/../../../lambda/build/${each.key}.zip") : ""
  runtime          = "python3.10"
  timeout          = 30
  memory_size      = 512

  layers = [aws_lambda_layer_version.shared.arn]

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      SECRETS_ARN   = var.secrets_arn
      DB_HOST       = var.rds_endpoint
      DB_NAME       = var.rds_db_name
      RABBITMQ_HOST = var.rabbitmq_endpoint
      S3_BUCKET     = var.s3_bucket_name
      QUEUE_NAME    = "telemetry-queue"
      ENVIRONMENT   = var.environment
    }
  }

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-${each.key}"
  }
}

# API Gateway v2 (HTTP API)
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "X-Requested-With"]
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 7
}

# API Gateway Integrations and Routes
resource "aws_lambda_permission" "api_gateway" {
  for_each = toset(local.lambda_functions)

  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions[each.key].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "lambda" {
  for_each = toset(local.lambda_functions)

  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.functions[each.key].invoke_arn
}

# Define routes based on Azure implementation
locals {
  routes = {
    users = [
      "POST /api/user",
      "GET /api/user",
      "PUT /api/user",
      "PATCH /api/user",
      "DELETE /api/user",
      "POST /api/user/login"
    ]
    devices = [
      "POST /api/device",
      "GET /api/devices",
      "PUT /api/device",
      "PATCH /api/device",
      "DELETE /api/device"
    ]
    telemetry = [
      "POST /api/telemetry",
      "GET /api/telemetry",
      "DELETE /api/telemetry"
    ]
    conditions = [
      "POST /api/conditions",
      "GET /api/conditions",
      "PUT /api/conditions",
      "DELETE /api/conditions"
    ]
    alertlogs = [
      "GET /api/alertlogs",
      "DELETE /api/alertlogs"
    ]
    admin = [
      "GET /api/manage/users",
      "PUT /api/manage/change-user-type",
      "POST /api/manage/create-admin",
      "GET /api/manage/processed-images",
      "POST /api/manage/transfer-device"
    ]
  }
}

resource "aws_apigatewayv2_route" "routes" {
  for_each = merge([
    for func, routes in local.routes : {
      for route in routes :
      "${func}-${replace(replace(route, " ", "-"), "/", "-")}" => {
        route_key      = route
        integration_id = aws_apigatewayv2_integration.lambda[func].id
      }
    }
  ]...)

  api_id    = aws_apigatewayv2_api.main.id
  route_key = each.value.route_key
  target    = "integrations/${each.value.integration_id}"
}

# ============================================
# RABBITMQ CONSUMER LAMBDA
# ============================================
# Separate Lambda for processing RabbitMQ messages
# Triggered by CloudWatch Events on a schedule

resource "aws_lambda_function" "consumer" {
  filename         = "${path.module}/../../../lambda/build/consumers.zip"
  function_name    = "${var.project_name}-${var.environment}-consumer"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.main"
  source_code_hash = fileexists("${path.module}/../../../lambda/build/consumers.zip") ? filebase64sha256("${path.module}/../../../lambda/build/consumers.zip") : ""
  runtime          = "python3.10"
  timeout          = 60 # Longer timeout for batch processing
  memory_size      = 512

  layers = [aws_lambda_layer_version.shared.arn]

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      SECRETS_ARN   = var.secrets_arn
      DB_HOST       = var.rds_endpoint
      DB_NAME       = var.rds_db_name
      RABBITMQ_HOST = var.rabbitmq_endpoint
      S3_BUCKET     = var.s3_bucket_name
      QUEUE_NAME    = "telemetry-queue"
      ENVIRONMENT   = var.environment
    }
  }

  lifecycle {
    ignore_changes = [source_code_hash]
  }

  tags = {
    Name    = "${var.project_name}-${var.environment}-consumer"
    Purpose = "RabbitMQ message consumer"
  }
}

# CloudWatch Events Rule - triggers consumer every minute
resource "aws_cloudwatch_event_rule" "consumer_schedule" {
  name                = "${var.project_name}-${var.environment}-consumer-schedule"
  description         = "Triggers RabbitMQ consumer Lambda every minute"
  schedule_expression = "rate(1 minute)"

  tags = {
    Name = "${var.project_name}-${var.environment}-consumer-schedule"
  }
}

resource "aws_cloudwatch_event_target" "consumer_target" {
  rule      = aws_cloudwatch_event_rule.consumer_schedule.name
  target_id = "ConsumerLambda"
  arn       = aws_lambda_function.consumer.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.consumer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.consumer_schedule.arn
}
