resource "aws_ecr_repository" "ml_platform_api" {
  name                 = var.ecr_repository_name
  image_tag_mutability = var.ecr_image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.ecr_scan_on_push
  }

  encryption_configuration {
    encryption_type = var.ecr_encryption_type
  }

  # tags = {
  #  Project     = var.project_name
  #  Environment = var.environment
  #  ManagedBy   = "terraform"
  #}
}