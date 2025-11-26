output "api_gateway_url" {
  value = aws_apigatewayv2_stage.default.invoke_url
}

output "function_names" {
  value = concat(
    [for f in aws_lambda_function.functions : f.function_name],
    [aws_lambda_function.consumer.function_name]
  )
}

output "consumer_function_name" {
  value = aws_lambda_function.consumer.function_name
}

output "security_group_id" {
  value = aws_security_group.lambda.id
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_exec.arn
}

output "layer_arn" {
  value = aws_lambda_layer_version.shared.arn
}
