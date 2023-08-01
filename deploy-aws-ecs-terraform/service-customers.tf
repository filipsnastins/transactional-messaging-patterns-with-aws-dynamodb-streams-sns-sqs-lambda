resource "aws_ecr_repository" "service_customers" {
  name = "${var.environment}-tomodachi-transactional-outbox-service-customers"
}

resource "aws_lb_target_group" "service_customers" {
  name        = "${var.environment}-t-outbox--customers-tg"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_default_vpc.default_vpc.id
  health_check {
    matcher  = "200"
    path     = "/customers/health"
    timeout  = 5
    interval = 10
  }
}

resource "aws_lb_listener_rule" "service_customers" {
  listener_arn = aws_lb_listener.listener.arn

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service_customers.arn
  }

  condition {
    path_pattern {
      values = ["/customer*"]
    }
  }
}

resource "aws_ecs_task_definition" "service_customers" {
  family                   = "${var.environment}-tomodachi-transactional-outbox--service-customers"
  container_definitions    = <<DEFINITION
  [
    {
      "name": "service-customers",
      "image": "${aws_ecr_repository.service_customers.repository_url}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 9700,
          "hostPort": 9700
        }
      ],
      "memory": 512,
      "cpu": 256,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${var.environment}-tomodachi-transactional-outbox--service-customers",
          "awslogs-region": "${var.region}",
          "awslogs-create-group": "true",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        { "name": "AWS_REGION", "value": "${var.region}" },
        { "name": "AWS_SNS_TOPIC_PREFIX", "value": "${var.environment}" },
        { "name": "AWS_SQS_QUEUE_NAME_PREFIX", "value": "${var.environment}" },
        { "name": "DYNAMODB_AGGREGATE_TABLE_NAME", "value": "${var.environment}-customers" },
        { "name": "DYNAMODB_OUTBOX_TABLE_NAME", "value": "${var.environment}-customers-outbox" }
      ]
    }
  ]
  DEFINITION
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = 512
  cpu                      = 256
  execution_role_arn       = aws_iam_role.ecsTaskExecutionRole.arn
  task_role_arn            = aws_iam_role.ecsTaskRole.arn
}

resource "aws_ecs_service" "service_customers" {
  name            = "service-customers"
  cluster         = aws_ecs_cluster.default.id
  task_definition = aws_ecs_task_definition.service_customers.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  load_balancer {
    target_group_arn = aws_lb_target_group.service_customers.arn
    container_name   = "service-customers"
    container_port   = 9700
  }

  network_configuration {
    subnets          = [aws_default_subnet.default_subnet_a.id, aws_default_subnet.default_subnet_b.id, aws_default_subnet.default_subnet_c.id]
    assign_public_ip = true
    security_groups  = [aws_security_group.service_security_group.id]
  }

  service_connect_configuration {
    enabled = true

    log_configuration {
      log_driver = "awslogs"
      options = {
        awslogs-group         = "/ecs/${var.environment}-tomodachi-transactional-outbox--service-customers",
        awslogs-region        = var.region,
        awslogs-create-group  = "true",
        awslogs-stream-prefix = "ecs"
      }
    }
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}
