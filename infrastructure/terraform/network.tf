data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

resource "aws_security_group" "api" {
  name        = var.security_group_name
  description = "Security group for ML Platform API"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Allow FastAPI requests from my IP"
    from_port   = var.container_port
    to_port     = var.container_port
    protocol    = "tcp"
    cidr_blocks = [var.allowed_client_cidr]
  }

  egress {
    description = "Allow outbound HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.egress_https_cidr]
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}