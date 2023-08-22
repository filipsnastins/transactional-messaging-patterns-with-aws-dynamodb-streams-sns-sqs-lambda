locals {
  full_service_name = "${var.environment}-service-${var.service_name}"
}

# SNS/SQS
module "sns_topic" {
  source   = "../sns-create-topic"
  for_each = toset(var.create_sns_topics)

  environment = var.environment
  topic_name  = each.key
}

module "sqs_queue" {
  source   = "../sqs-create-and-subscribe-queue"
  for_each = tomap({ for t in var.create_and_subscribe_sqs_queues : t.queue => t })

  environment            = var.environment
  queue_name             = each.value.queue
  subscribe_to_sns_topic = each.value.topic
}

# IAM Task Role
module "ecs_service_iam_task_role" {
  source = "../ecs-service-iam-task-role"

  environment  = var.environment
  service_name = var.service_name

  dynamodb_table_arns = var.dynamodb_table_arns
  sns_topic_arns      = [for sns_topic in module.sns_topic : sns_topic.arn]
  sqs_queue_arns      = [for sqs_queue in module.sqs_queue : sqs_queue.arn]
}

# Elastic Container Registry
# tfsec:ignore:aws-ecr-enforce-immutable-repository
resource "aws_ecr_repository" "default" {
  name = local.full_service_name
}

# Elastic Application Load Balancer
resource "aws_lb_target_group" "default" {
  name        = "${local.full_service_name}--tg"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    matcher  = "200"
    path     = var.http_healthcheck_path
    timeout  = 5
    interval = 10
  }
}

resource "aws_lb_listener_rule" "default" {
  listener_arn = var.alb_listener_arn

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.default.arn
  }

  condition {
    path_pattern {
      values = [var.http_listen_path_pattern]
    }
  }
}

# Elastic Container Service - task definition
resource "aws_ecs_task_definition" "default" {
  family                = local.full_service_name
  container_definitions = <<DEFINITION
  [
    {
      "name": "service-${var.service_name}",
      "image": "${aws_ecr_repository.default.repository_url}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": ${var.container_port},
          "hostPort": ${var.container_port}
        }
      ],
      "memory": ${var.memory},
      "cpu": ${var.cpu},
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${local.full_service_name}",
          "awslogs-region": "${var.region}",
          "awslogs-create-group": "true",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": ${jsonencode(var.environment_variables)}
    }
  ]
  DEFINITION

  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  memory = var.memory
  cpu    = var.cpu

  execution_role_arn = var.ecs_task_execution_role_arn
  task_role_arn      = module.ecs_service_iam_task_role.arn
}

# Elastic Container Service - service
resource "aws_ecs_service" "default" {
  name            = "service-${var.service_name}"
  cluster         = var.ecs_cluster_id
  task_definition = "${aws_ecs_task_definition.default.arn_without_revision}:${var.revision}"
  launch_type     = "FARGATE"

  desired_count = var.replicas

  load_balancer {
    target_group_arn = aws_lb_target_group.default.arn
    container_name   = "service-${var.service_name}"
    container_port   = var.container_port
  }

  network_configuration {
    subnets          = var.vpc_subnet_ids
    assign_public_ip = true
    security_groups  = [var.security_group_id]
  }

  service_connect_configuration {
    enabled = true

    log_configuration {
      log_driver = "awslogs"
      options = {
        awslogs-group         = "/ecs/${local.full_service_name}",
        awslogs-region        = var.region,
        awslogs-create-group  = "true",
        awslogs-stream-prefix = "ecs"
      }
    }
  }
}
