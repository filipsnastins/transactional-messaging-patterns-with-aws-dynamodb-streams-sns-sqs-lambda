locals {
  message_retention_seconds = 1209600 # 14 days
}

resource "aws_sqs_queue" "source_queue" {
  name = "${var.environment}-${var.queue_name}"

  message_retention_seconds = local.message_retention_seconds
}

resource "aws_sqs_queue" "dead_letter_queue" {
  name = "${var.environment}-${var.queue_name}--dlq"

  message_retention_seconds = local.message_retention_seconds

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue",
    sourceQueueArns   = [aws_sqs_queue.source_queue.arn]
  })
}

resource "aws_sqs_queue_redrive_policy" "default" {
  queue_url = aws_sqs_queue.source_queue.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter_queue.arn
    maxReceiveCount     = 3
  })
}

module "sns_topic" {
  source = "../sns-create-topic"

  environment = var.environment
  topic_name  = var.subscribe_to_sns_topic
}

resource "aws_sns_topic_subscription" "default" {
  topic_arn = module.sns_topic.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.source_queue.arn
}
