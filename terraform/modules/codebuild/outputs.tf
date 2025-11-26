# ============================================
# CodeBuild Module Outputs
# ============================================

output "project_name" {
  description = "CodeBuild project name"
  value       = aws_codebuild_project.db_migrate.name
}

output "project_arn" {
  description = "CodeBuild project ARN"
  value       = aws_codebuild_project.db_migrate.arn
}

output "security_group_id" {
  description = "CodeBuild security group ID"
  value       = aws_security_group.codebuild.id
}

output "role_arn" {
  description = "CodeBuild IAM role ARN"
  value       = aws_iam_role.codebuild.arn
}

output "log_group_name" {
  description = "CloudWatch log group for build logs"
  value       = aws_cloudwatch_log_group.codebuild.name
}
