resource "aws_cloudwatch_log_group" "api" {
  name              = var.log_group_name
  retention_in_days = var.log_retention_days

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}