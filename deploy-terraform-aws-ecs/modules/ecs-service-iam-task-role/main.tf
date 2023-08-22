module "ecs_assume_role_policy" {
  source = "../ecs-assume-role-policy"
}

resource "aws_iam_role" "default" {
  name               = "role-${var.environment}-service-${var.service_name}"
  description        = "Task role for running ECS tasks"
  assume_role_policy = module.ecs_assume_role_policy.json
}

module "policy_service_dynamodb" {
  source = "../policy-service-dynamodb"

  environment  = var.environment
  service_name = var.service_name

  role_name           = aws_iam_role.default.name
  dynamodb_table_arns = var.dynamodb_table_arns

  count = length(var.dynamodb_table_arns) > 0 ? 1 : 0
}

module "policy_service_sns" {
  source = "../policy-service-sns"

  environment  = var.environment
  service_name = var.service_name

  role_name      = aws_iam_role.default.name
  sns_topic_arns = var.sns_topic_arns

  count = length(var.sns_topic_arns) > 0 ? 1 : 0
}

module "policy_service_sqs" {
  source = "../policy-service-sqs"

  environment  = var.environment
  service_name = var.service_name

  role_name      = aws_iam_role.default.name
  sqs_queue_arns = var.sqs_queue_arns

  count = length(var.sqs_queue_arns) > 0 ? 1 : 0
}
