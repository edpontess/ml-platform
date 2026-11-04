variable "aws_region" {
  type    = string
  default = "eu-north-1"
}

variable "aws_profile" {
  type    = string
  default = "ml-platform"
}

variable "allowed_client_cidr" {
  description = "Public IPv4 address allowed to access FastAPI, using /32 notation"
  type        = string

  validation {
    condition     = can(cidrhost(var.allowed_client_cidr, 0)) && endswith(var.allowed_client_cidr, "/32")
    error_message = "Provide a valid IPv4 address with a /32 prefix."
  }
}
variable "project_name" {
  type    = string
  default = "ml-platform"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "ecr_repository_name" {
  type    = string
  default = "ml-platform-api"
}

variable "ecr_image_tag_mutability" {
  type    = string
  default = "MUTABLE"
}

variable "ecr_scan_on_push" {
  type    = bool
  default = false
}

variable "ecr_encryption_type" {
  type    = string
  default = "AES256"
}

variable "image_tag" {
  type    = string
  default = "v1"
}

variable "log_group_name" {
  type    = string
  default = "/ecs/ml-platform-api"
}

variable "log_retention_days" {
  type    = number
  default = 7
}

variable "log_stream_prefix" {
  type    = string
  default = "ecs"
}

variable "ecs_cluster_name" {
  type    = string
  default = "ml-platform-cluster"
}

variable "ecs_service_name" {
  type    = string
  default = "ml-platform-api-service"
}

variable "task_family" {
  type    = string
  default = "ml-platform-api"
}

variable "container_name" {
  type    = string
  default = "ml-platform-api"
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "task_cpu" {
  type    = string
  default = "512"
}

variable "task_memory" {
  type    = string
  default = "1024"
}

variable "task_operating_system_family" {
  type    = string
  default = "LINUX"
}

variable "task_cpu_architecture" {
  type    = string
  default = "ARM64"
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "assign_public_ip" {
  type    = bool
  default = true
}

variable "ecs_execution_role_name" {
  type    = string
  default = "ml-platform-ecs-execution"
}

variable "ecs_execution_policy_arn" {
  type    = string
  default = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

variable "security_group_name" {
  type    = string
  default = "ml-platform-api-sg"
}

variable "egress_https_cidr" {
  description = "CIDR allowed for outbound HTTPS"
  type        = string
  default     = "0.0.0.0/0"
}
