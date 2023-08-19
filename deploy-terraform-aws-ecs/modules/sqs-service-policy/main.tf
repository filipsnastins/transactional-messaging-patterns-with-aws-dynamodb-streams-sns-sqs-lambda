locals {
  source_queue_statements = [for sqs_topic_arn in var.sqs_queue_arns : {
    "Effect" : "Allow",
    "Action" : ["sqs:*"],
    "Resource" : sqs_topic_arn
  }]

  dead_letter_queue_statements = [for sqs_topic_arn in var.sqs_queue_arns : {
    "Effect" : "Allow",
    "Action" : ["sqs:*"],
    "Resource" : "${sqs_topic_arn}--dlq"
  }]
}

resource "aws_iam_role_policy" "default" {
  name = "${var.environment}-service-${var.service_name}--sqs"

  role = var.role_name

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : concat(local.source_queue_statements, local.dead_letter_queue_statements)
  })
}
