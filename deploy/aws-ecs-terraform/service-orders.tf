resource "aws_ecs_task_definition" "service_orders" {
  family                   = "${var.environment}-tomodachi-transactional-outbox--service-orders"
  container_definitions    = <<DEFINITION
  [
    {
      "name": "${var.environment}-tomodachi-transactional-outbox--service-orders",
      "image": "${aws_ecr_repository.service_orders.repository_url}",
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
          "awslogs-group": "/ecs/${var.environment}-tomodachi-transactional-outbox--service-orders",
          "awslogs-region": "eu-west-1",
          "awslogs-create-group": "true",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        { "name": "AWS_REGION", "value": "eu-west-1" },
        { "name": "AWS_SNS_TOPIC_PREFIX", "value": "${var.environment}" },
        { "name": "AWS_SQS_QUEUE_NAME_PREFIX", "value": "${var.environment}" },
        { "name": "DYNAMODB_AGGREGATE_TABLE_NAME", "value": "${var.environment}-orders" },
        { "name": "DYNAMODB_OUTBOX_TABLE_NAME", "value": "${var.environment}-orders-outbox" }
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

resource "aws_ecs_service" "service_orders" {
  name            = "service-orders"
  cluster         = aws_ecs_cluster.default.id
  task_definition = aws_ecs_task_definition.service_orders.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  load_balancer {
    target_group_arn = aws_lb_target_group.target_group.arn
    container_name   = aws_ecs_task_definition.service_orders.family
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
        awslogs-group         = "/ecs/${var.environment}-tomodachi-transactional-outbox--service-orders",
        awslogs-region        = "eu-west-1",
        awslogs-create-group  = "true",
        awslogs-stream-prefix = "ecs"
      }
    }
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}
