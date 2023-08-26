resource "aws_sqs_queue" "default" {
  name                      = "${var.environment}-${var.queue_name}"
  message_retention_seconds = 1209600 # 14 days
}
