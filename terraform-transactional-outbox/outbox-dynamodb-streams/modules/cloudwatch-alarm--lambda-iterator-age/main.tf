resource "aws_cloudwatch_metric_alarm" "default" {
  alarm_name        = "${var.function_name} - Iterator Age too old"
  alarm_description = "If IteratorAge is too old, it means that the Lambda Outbox function is not dispatching messages fast enough."

  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 30000 # milliseconds
  period              = 120   # seconds
  treat_missing_data  = "missing"

  namespace   = "AWS/Lambda"
  metric_name = "IteratorAge"
  statistic   = "Maximum"

  dimensions = {
    "FunctionName" = var.function_name
  }
}
