locals {
  function_name = "outbox-dynamodb-streams--${var.service_name}"
}

# DynamoDB Outbox Table
module "dynamodb_outbox_table" {
  source = "./modules/dynamodb-table-outbox"

  environment  = var.environment
  service_name = var.service_name
}

# SNS topics to which the Lambda will publish messages
module "sns_topics" {
  source   = "./modules/sns-topic"
  for_each = toset(var.create_sns_topics)

  environment = var.environment
  topic_name  = each.key
}

# SQS Dead Letter Queue for failed Lambda invocations
module "lambda_sqs_dlq" {
  source = "./modules/sqs-queue"

  environment = var.environment
  queue_name  = "${local.function_name}--dlq"
}

# IAM Role for Lambda
module "lambda_iam_role" {
  source = "./modules/lambda-iam-role"

  function_name             = "${var.environment}-${local.function_name}"
  dynamodb_table_arn        = module.dynamodb_outbox_table.arn
  dynamodb_table_stream_arn = module.dynamodb_outbox_table.stream_arn
  sns_topic_arns            = [for sns_topic in module.sns_topics : sns_topic.arn]
  sqs_queue_arns            = [module.lambda_sqs_dlq.arn]
}

# Lambda source code path
data "local_file" "lambda_source_zip" {
  filename = var.lambda_source_zip_path
}

# Lambda Function
resource "aws_lambda_function" "default" {
  function_name = "${var.environment}-${local.function_name}"
  description   = "Transactional Outbox publisher - listens to DynamoDB Streams and publishes messages to SNS"

  role = module.lambda_iam_role.arn

  package_type     = "Zip"
  filename         = data.local_file.lambda_source_zip.filename
  source_code_hash = data.local_file.lambda_source_zip.content_base64sha256

  runtime       = "python3.10"
  handler       = "app.lambda_function.lambda_handler"
  architectures = [var.architecture]

  memory_size = var.memory_size
  timeout     = var.timeout

  environment {
    variables = {
      AWS_SNS_TOPIC_PREFIX       = "${var.environment}-"
      DYNAMODB_OUTBOX_TABLE_NAME = module.dynamodb_outbox_table.name
    }
  }

  dead_letter_config {
    target_arn = module.lambda_sqs_dlq.arn
  }

  tracing_config {
    mode = "Active"
  }
}

resource "aws_lambda_function_event_invoke_config" "default" {
  function_name                = aws_lambda_function.default.function_name
  maximum_event_age_in_seconds = var.maximum_event_age_in_seconds
  maximum_retry_attempts       = 2
}

# Event Source Mapping; DynamoDB Streams --> Lambda
resource "aws_lambda_event_source_mapping" "default" {
  event_source_arn = module.dynamodb_outbox_table.stream_arn
  function_name    = aws_lambda_function.default.arn

  enabled           = true
  starting_position = "LATEST"

  function_response_types = ["ReportBatchItemFailures"]

  batch_size             = var.batch_size
  maximum_retry_attempts = var.maximum_retry_attempts
  parallelization_factor = var.parallelization_factor

  destination_config {
    on_failure {
      destination_arn = module.lambda_sqs_dlq.arn
    }
  }
}

# CloudWatch Alarms
module "cloudwatch_alarm__lambda_iterator_age" {
  source = "./modules/cloudwatch-alarm--lambda-iterator-age"

  function_name = aws_lambda_function.default.function_name
}


module "cloudwatch_alarm__lambda_sqs_dlq" {
  source = "./modules/cloudwatch-alarm--sqs-dlq"

  sqs_dlq_name = module.lambda_sqs_dlq.name
}
