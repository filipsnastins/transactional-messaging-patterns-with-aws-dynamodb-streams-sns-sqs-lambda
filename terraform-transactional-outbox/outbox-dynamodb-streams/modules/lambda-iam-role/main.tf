module "lambda_assume_role_policy" {
  source = "../lambda-assume-role-policy"
}

resource "aws_iam_role" "default" {
  assume_role_policy = module.lambda_assume_role_policy.json
  name               = "role-${var.function_name}"
}

resource "aws_iam_role_policy_attachment" "aws_lambda_basic_execution_role" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.default.name
}

module "policy_dynamodb" {
  source = "../policy-dynamodb"

  role_name                 = aws_iam_role.default.name
  function_name             = var.function_name
  dynamodb_table_arn        = var.dynamodb_table_arn
  dynamodb_table_stream_arn = var.dynamodb_table_stream_arn
}

module "policy_sns" {
  source = "../policy-sns"

  role_name      = aws_iam_role.default.name
  function_name  = var.function_name
  sns_topic_arns = var.sns_topic_arns
}

module "policy_sqs" {
  source = "../policy-sqs"

  role_name      = aws_iam_role.default.name
  function_name  = var.function_name
  sqs_queue_arns = var.sqs_queue_arns
}

module "policy_xray" {
  source = "../policy-xray"

  role_name     = aws_iam_role.default.name
  function_name = var.function_name
}
