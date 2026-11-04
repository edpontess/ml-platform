resource "aws_ecs_cluster" "main" {
  name = "ml-platform-cluster"
}

resource "aws_ecs_task_definition" "api" {
  family                   = "ml-platform-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = "512"
  memory = "1024"

  execution_role_arn = aws_iam_role.ecs_execution.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  container_definitions = jsonencode([
    {
      name      = "ml-platform-api"
      image     = "974268348848.dkr.ecr.eu-north-1.amazonaws.com/ml-platform-api:v1"
      essential = true

      portMappings = [{
        containerPort = 8000
        protocol      = "tcp"
      }]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "api" {
  name            = "ml-platform-api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = true
  }

  tags = {
    Project     = "ml-platform"
    Environment = "dev"
  }
}