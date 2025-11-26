# Telemetry bucket outputs
output "bucket_name" { value = aws_s3_bucket.telemetry.id }
output "bucket_arn" { value = aws_s3_bucket.telemetry.arn }
output "bucket_domain_name" { value = aws_s3_bucket.telemetry.bucket_domain_name }

# Artifacts bucket outputs
output "artifacts_bucket_name" { value = aws_s3_bucket.artifacts.id }
output "artifacts_bucket_arn" { value = aws_s3_bucket.artifacts.arn }
