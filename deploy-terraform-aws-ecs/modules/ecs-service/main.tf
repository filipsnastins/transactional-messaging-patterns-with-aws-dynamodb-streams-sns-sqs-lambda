resource "aws_ecr_repository" "default" {
  name = "${var.environment}-service-${var.service_name}"
}

resource "aws_lb_target_group" "default" {
  name        = "${var.environment}-service-${var.service_name}--tg"
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

resource "aws_ecs_task_definition" "default" {
  family                   = "${var.environment}-service-${var.service_name}"
  container_definitions    = <<DEFINITION
  [
    {
      "name": "service-${var.service_name}",
      "image": "${aws_ecr_repository.default.repository_url}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": ${var.port},
          "hostPort": ${var.port}
        }
      ],
      "memory": ${var.memory},
      "cpu": ${var.cpu},
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${var.environment}-service-${var.service_name}",
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
  memory                   = var.memory
  cpu                      = var.cpu
  execution_role_arn       = var.ecs_task_execution_role_arn
  # task_role_arn            = aws_iam_role.ecsTaskRole.arn # TODO
}

resource "aws_ecs_service" "default" {
  name            = "service-${var.service_name}"
  cluster         = var.ecs_cluster_id
  task_definition = aws_ecs_task_definition.default.arn
  launch_type     = "FARGATE"
  desired_count   = var.replicas

  load_balancer {
    target_group_arn = aws_lb_target_group.default.arn
    container_name   = "service-${var.service_name}"
    container_port   = var.port
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
        awslogs-group         = "/ecs/${var.environment}-service-${var.service_name}",
        awslogs-region        = var.region,
        awslogs-create-group  = "true",
        awslogs-stream-prefix = "ecs"
      }
    }
  }
}
