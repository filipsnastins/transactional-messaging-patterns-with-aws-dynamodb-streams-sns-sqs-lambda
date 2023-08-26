resource "aws_sns_topic" "default" {
  name = "${var.environment}-${var.topic_name}"
}
