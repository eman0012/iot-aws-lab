output "policy_name" { value = aws_iot_policy.device_policy.name }
output "policy_arn" { value = aws_iot_policy.device_policy.arn }
output "topic_rule_arn" { value = aws_iot_topic_rule.telemetry.arn }
