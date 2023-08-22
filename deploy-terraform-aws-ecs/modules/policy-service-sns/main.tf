resource "aws_iam_role_policy" "default" {
  name = "policy-${var.environment}-service-${var.service_name}--sns"

  role = var.role_name

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : ["sns:*"],
        "Resource" : [for sns_topic_arn in var.sns_topic_arns : sns_topic_arn]
      }
    ]
  })
}
