module "service_orders_ecs" {
  source = "../modules/ecs-service"

  region       = var.region
  environment  = var.environment
  service_name = "orders"

  revision = null

  container_port    = 9700
  vpc_id            = module.vpc.id
  vpc_subnet_ids    = module.vpc.subnet_ids
  alb_listener_arn  = module.alb.listener_arn
  security_group_id = module.alb.service_security_group_id

  ecs_cluster_id              = module.ecs_cluster.id
  ecs_task_execution_role_arn = module.ecs_iam_task_execution_role.arn

  cpu      = 256
  memory   = 512
  replicas = 1

  http_listen_path_pattern = "/order*"
  http_healthcheck_path    = "/orders/health"

  environment_variables = [
    { "name" : "ENVIRONMENT", "value" : var.environment },
    { "name" : "AWS_REGION", "value" : var.region },
    { "name" : "AWS_SNS_TOPIC_PREFIX", "value" : "${var.environment}-" },
    { "name" : "AWS_SQS_QUEUE_NAME_PREFIX", "value" : "${var.environment}-" },
    { "name" : "DYNAMODB_ORDERS_TABLE_NAME", "value" : aws_dynamodb_table.orders.name },
    { "name" : "DYNAMODB_INBOX_TABLE_NAME", "value" : module.service_orders_inbox_table.name },
    { "name" : "DYNAMODB_OUTBOX_TABLE_NAME", "value" : module.service_orders_outbox_dynamodb_streams.dynamodb_outbox_table_name },
  ]

  dynamodb_table_arns = [
    aws_dynamodb_table.orders.arn,
    module.service_orders_inbox_table.arn,
    module.service_orders_outbox_dynamodb_streams.dynamodb_outbox_table_arn,
  ]

  create_sns_topics = [
    "customer--credit-reservation-failed",
    "customer--credit-reserved",
    "customer--validation-failed",
  ]

  create_and_subscribe_sqs_queues = [
    { "topic" : "customer--credit-reserved", queue = "order--customer-credit-reserved" },
    { "topic" : "customer--credit-reservation-failed", queue = "order--customer-credit-reservation-failed" },
    { "topic" : "customer--validation-failed", queue = "order--customer-validation-failed" },
  ]
}

resource "aws_dynamodb_table" "orders" {
  name         = "${var.environment}-orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"

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

module "service_orders_inbox_table" {
  source = "../../terraform-transactional-messaging/idempotent-consumer-dynamodb-inbox"

  environment  = var.environment
  service_name = "orders"
}

module "service_orders_outbox_dynamodb_streams" {
  source = "../../terraform-transactional-messaging/outbox-dynamodb-streams"

  environment  = var.environment
  service_name = "orders"

  create_sns_topics = [
    "order--approved",
    "order--cancelled",
    "order--created",
    "order--rejected",
  ]
}
