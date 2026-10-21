resource "aws_ecr_repository" "ml_platform_api" {
  name                 = "ml-platform-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Project     = "ml-platform"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}