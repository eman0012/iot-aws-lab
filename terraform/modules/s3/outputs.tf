output "bucket_name" { value = aws_s3_bucket.telemetry.id }
output "bucket_arn" { value = aws_s3_bucket.telemetry.arn }
output "bucket_domain_name" { value = aws_s3_bucket.telemetry.bucket_domain_name }
