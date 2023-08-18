locals {
  orders_table_name = "${var.environment}-orders"
}

module "service_orders_ecs" {
  source = "../modules/ecs-service"

  region      = var.region
  environment = var.environment

  service_name   = "orders"
  port           = 9700
  vpc_id         = module.vpc.id
  vpc_subnet_ids = module.vpc.subnet_ids

  alb_listener_arn  = module.alb.listener_arn
  security_group_id = module.alb.service_security_group_id

  ecs_cluster_id              = module.ecs_cluster.id
  ecs_task_execution_role_arn = module.ecs_iam_policy.ecs_task_execution_role_arn

  memory   = 512
  cpu      = 256
  replicas = 1

  http_healthcheck_path    = "/orders/health"
  http_listen_path_pattern = "/order*"

  environment_variables = [
    { "name" : "ENVIRONMENT", "value" : var.environment },
    { "name" : "AWS_REGION", "value" : var.region },
    { "name" : "AWS_SNS_TOPIC_PREFIX", "value" : var.environment },
    { "name" : "AWS_SQS_QUEUE_NAME_PREFIX", "value" : var.environment },
    { "name" : "DYNAMODB_ORDERS_TABLE_NAME", "value" : aws_dynamodb_table.service_orders_dynamodb_table.name },
    { "name" : "DYNAMODB_INBOX_TABLE_NAME", "value" : module.service_orders_dynamodb_inbox_table.name },
    { "name" : "DYNAMODB_OUTBOX_TABLE_NAME", "value" : module.service_orders_dynamodb_outbox_table.name },
  ]
}

resource "aws_dynamodb_table" "service_orders_dynamodb_table" {
  name         = local.orders_table_name
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "PK"

  attribute {
    name = "PK"
    type = "S"
  }
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
