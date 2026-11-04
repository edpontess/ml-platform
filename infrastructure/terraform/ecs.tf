resource "aws_ecs_cluster" "main" {
  name = var.ecs_cluster_name
}

resource "aws_ecs_task_definition" "api" {
  family                   = var.task_family
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = var.task_cpu
  memory = var.task_memory

  execution_role_arn = aws_iam_role.ecs_execution.arn

  runtime_platform {
    operating_system_family = var.task_operating_system_family
    cpu_architecture        = var.task_cpu_architecture
  }

  container_definitions = jsonencode([
    {
      name      = var.container_name
      image     = "${aws_ecr_repository.ml_platform_api.repository_url}:${var.image_tag}"
      essential = true

      portMappings = [{
        containerPort = var.container_port
        protocol      = "tcp"
      }]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = var.log_stream_prefix
        }
      }
    }
  ])
}

resource "aws_ecs_service" "api" {
  name            = var.ecs_service_name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn

  desired_count = var.desired_count
  launch_type   = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = var.assign_public_ip
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}