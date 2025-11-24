output "broker_id" { value = aws_mq_broker.rabbitmq.id }
output "broker_arn" { value = aws_mq_broker.rabbitmq.arn }
output "broker_endpoint" { value = aws_mq_broker.rabbitmq.instances[0].endpoints[0] }
output "console_url" { value = aws_mq_broker.rabbitmq.instances[0].console_url }
output "security_group_id" { value = aws_security_group.rabbitmq.id }
