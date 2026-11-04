resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/ml-platform-api"
  retention_in_days = 7

  tags = {
    Project     = "ml-platform"
    Environment = "dev"
  }
}