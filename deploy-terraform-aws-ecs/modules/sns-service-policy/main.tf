resource "aws_iam_role_policy" "default" {
  name = "${var.environment}-service-${var.service_name}--sns"

  role = var.role_name

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      for sns_topic_arn in var.sns_topic_arns : {
        "Effect" : "Allow",
        "Action" : ["sns:*"],
        "Resource" : sns_topic_arn
      }
    ]
  })
}
