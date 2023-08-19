# SNS Topics
module "sns_topic" {
  source   = "../sns-create-topic"
  for_each = toset(var.create_sns_topics)

  environment = var.environment
  topic_name  = each.key
}

# SQS Dead Letter Queue
resource "aws_sqs_queue" "dead_letter_queue" {
  name = "${var.environment}-dynamodb-streams-outbox--${var.service_name}--dlq"

  message_retention_seconds = 1209600 # 14 days
  # kms_master_key_id         = "alias/aws/sqs"
}

# IAM Role
module "lambda_assume_role_policy" {
  source = "../lambda-assume-role-policy"
}

resource "aws_iam_role" "default" {
  assume_role_policy = module.lambda_assume_role_policy.json
  name               = "${var.environment}-dynamodb-streams-outbox--${var.service_name}"
}

resource "aws_iam_role_policy_attachment" "aws_lambda_basic_execution_role" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.default.name
}

resource "aws_iam_role_policy" "dynamodb_policy" {
  name = "${var.environment}-dynamodb-streams-outbox--${var.service_name}--dynamodb"

  role = aws_iam_role.default.name

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : ["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
        "Resource" : "*",
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem",
        ],
        "Resource" : var.dynamodb_outbox_table_arn,
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "dynamodb:DescribeStream",
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:ListStreams"
        ],
        "Resource" : var.dynamodb_outbox_table_stream_arn,
      },
    ],
  })
}

resource "aws_iam_role_policy" "sns_policy" {
  name = "${var.environment}-dynamodb-streams-outbox--${var.service_name}--sns"

  role = aws_iam_role.default.name

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      for sns_topic in module.sns_topic : {
        "Effect" : "Allow",
        "Action" : ["sns:CreateTopic", "sns:Publish"],
        "Resource" : sns_topic.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "sqs_policy" {
  name = "${var.environment}-dynamodb-streams-outbox--${var.service_name}--sqs"

  role = aws_iam_role.default.name

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : ["sqs:SendMessage"],
        "Resource" : aws_sqs_queue.dead_letter_queue.arn
      }
    ]
  })
}

# Lambda
data "local_file" "source" {
  filename = var.lambda_source_zip_path
}

resource "aws_lambda_function" "default" {
  function_name = "${var.environment}-dynamodb-streams-outbox--${var.service_name}"
  description   = "Transactional Outbox publisher - listens to DynamoDB Streams and publishes messages to SNS"

  role = aws_iam_role.default.arn

  package_type     = "Zip"
  filename         = data.local_file.source.filename
  source_code_hash = data.local_file.source.content_base64sha256

  runtime       = "python3.10"
  handler       = "app.lambda_function.lambda_handler"
  architectures = [var.architecture]

  memory_size = 256
  timeout     = 60

  environment {
    variables = {
      DYNAMODB_OUTBOX_TABLE_NAME = var.dynamodb_outbox_table_name
      AWS_SNS_TOPIC_PREFIX       = "${var.environment}-"
    }
  }

  dead_letter_config {
    target_arn = aws_sqs_queue.dead_letter_queue.arn
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
  event_source_arn = var.dynamodb_outbox_table_stream_arn
  function_name    = aws_lambda_function.default.arn

  enabled           = true
  starting_position = "LATEST"

  function_response_types = ["ReportBatchItemFailures"]

  batch_size             = var.batch_size
  maximum_retry_attempts = var.maximum_retry_attempts
  parallelization_factor = var.parallelization_factor

  destination_config {
    on_failure {
      destination_arn = aws_sqs_queue.dead_letter_queue.arn
    }
  }
}
