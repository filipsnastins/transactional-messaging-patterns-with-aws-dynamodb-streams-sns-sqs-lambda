resource "aws_iam_role_policy" "default" {
  name = "policy-${var.function_name}--sqs"

  role = var.role_name

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : ["sqs:SendMessage"],
        "Resource" : [for sqs_queue_arn in var.sqs_queue_arns : sqs_queue_arn]
      }
    ]
  })
}
