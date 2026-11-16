resource "aws_iam_user" "github_deploy" {
  name = "ml-platform-github-deploy"

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "github_deploy" {
  statement {
    sid       = "ECRAuthorization"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "ECRPush"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart"
    ]
    resources = [aws_ecr_repository.ml_platform_api.arn]
  }

  statement {
    sid = "ECSTaskDefinition"
    actions = [
      "ecs:RegisterTaskDefinition",
      "ecs:DescribeTaskDefinition"
    ]
    resources = ["*"]
  }

  statement {
    sid = "ECSDeployment"
    actions = [
      "ecs:UpdateService",
      "ecs:DescribeServices"
    ]
    resources = [aws_ecs_service.api.id]
  }

  statement {
    sid       = "PassECSExecutionRole"
    actions   = ["iam:PassRole"]
    resources = [aws_iam_role.ecs_execution.arn]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }

  statement {
    sid = "ReadChampionModel"

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.model_artifacts.arn}/champion/*"
    ]
  }

  statement {
    sid = "ListChampionModel"

    actions = [
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.model_artifacts.arn
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        "champion/",
        "champion/*"
      ]
    }
  }
}

resource "aws_iam_user_policy" "github_deploy" {
  name   = "ml-platform-github-deploy-policy"
  user   = aws_iam_user.github_deploy.name
  policy = data.aws_iam_policy_document.github_deploy.json
}