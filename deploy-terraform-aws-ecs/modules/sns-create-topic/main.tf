resource "aws_sns_topic" "default" {
  name = "${var.environment}-${var.topic_name}"
  # kms_master_key_id = "alias/aws/sns"
}
