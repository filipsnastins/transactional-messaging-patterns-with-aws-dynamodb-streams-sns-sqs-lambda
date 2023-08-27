resource "aws_cloudwatch_metric_alarm" "default" {
  alarm_name        = "${var.sqs_dlq_name} - messages in DLQ"
  alarm_description = "Alarm that monitors messages in the ${var.sqs_dlq_name}"

  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 0
  period              = 120
  unit                = "Count"
  treat_missing_data  = "missing"

  namespace   = "AWS/SQS"
  metric_name = "ApproximateNumberOfMessagesVisible"
  statistic   = "Sum"

  dimensions = {
    "QueueName" : var.sqs_dlq_name
  }
}
