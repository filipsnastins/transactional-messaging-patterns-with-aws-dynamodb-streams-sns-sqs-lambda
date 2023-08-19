locals {
  orders_table_name = "${var.environment}-orders"
}

# tfsec:ignore:aws-ecr-enforce-immutable-repository
module "service_orders_ecs" {
  source = "../modules/ecs-service"

  region      = var.region
  environment = var.environment

  revision = 9

  service_name   = "orders"
  container_port = 9700
  vpc_id         = module.vpc.id
  vpc_subnet_ids = module.vpc.subnet_ids

  alb_listener_arn  = module.alb.listener_arn
  security_group_id = module.alb.service_security_group_id

  ecs_cluster_id              = module.ecs_cluster.id
  ecs_task_execution_role_arn = module.ecs_iam_policy.ecs_task_execution_role_arn

  cpu      = 256
  memory   = 512
  replicas = 1

  http_healthcheck_path    = "/orders/health"
  http_listen_path_pattern = "/order*"

  environment_variables = [
    { "name" : "ENVIRONMENT", "value" : var.environment },
    { "name" : "AWS_REGION", "value" : var.region },
    { "name" : "AWS_SNS_TOPIC_PREFIX", "value" : "${var.environment}-" },
    { "name" : "AWS_SQS_QUEUE_NAME_PREFIX", "value" : "${var.environment}-" },
    { "name" : "DYNAMODB_ORDERS_TABLE_NAME", "value" : aws_dynamodb_table.service_orders_dynamodb_table.name },
    { "name" : "DYNAMODB_INBOX_TABLE_NAME", "value" : module.service_orders_dynamodb_inbox_table.name },
    { "name" : "DYNAMODB_OUTBOX_TABLE_NAME", "value" : module.service_orders_dynamodb_outbox_table.name },
  ]

  grant_dynamodb_permissions = [
    aws_dynamodb_table.service_orders_dynamodb_table.arn,
    module.service_orders_dynamodb_inbox_table.arn,
    module.service_orders_dynamodb_outbox_table.arn,
  ]

  create_sns_topics = [
    "order--approved",
    "order--cancelled",
    "order--created",
    "order--rejected",
    "customer--credit-reserved",
    "customer--credit-reservation-failed",
    "customer--validation-failed",
  ]

  create_and_subscribe_sqs_queues = [
    { "topic" : "customer--credit-reserved", queue = "order--customer-credit-reserved" },
    { "topic" : "customer--credit-reservation-failed", queue = "order--customer-credit-reservation-failed" },
    { "topic" : "customer--validation-failed", queue = "order--customer-validation-failed" },
  ]
}

resource "aws_dynamodb_table" "service_orders_dynamodb_table" {
  name         = local.orders_table_name
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "PK"

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  attribute {
    name = "PK"
    type = "S"
  }
}

module "service_orders_lambda_outbox_dynamodb_streams" {
  source = "../modules/lambda-outbox-dynamodb-streams"

  environment  = var.environment
  service_name = "orders"

  dynamodb_outbox_table_name       = module.service_orders_dynamodb_outbox_table.name
  dynamodb_outbox_table_arn        = module.service_orders_dynamodb_outbox_table.arn
  dynamodb_outbox_table_stream_arn = module.service_orders_dynamodb_outbox_table.stream_arn

  create_sns_topics = [
    "order--approved",
    "order--cancelled",
    "order--created",
    "order--rejected",
  ]
}

module "service_orders_dynamodb_inbox_table" {
  source = "../modules/dynamodb-table-idempotent-consumer-inbox"

  environment    = var.environment
  aggregate_name = "orders"
}

module "service_orders_dynamodb_outbox_table" {
  source = "../modules/dynamodb-table-transactional-outbox"

  environment    = var.environment
  aggregate_name = "orders"
}
