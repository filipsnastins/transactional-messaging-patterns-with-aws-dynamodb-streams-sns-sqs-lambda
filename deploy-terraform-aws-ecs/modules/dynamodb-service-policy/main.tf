resource "aws_iam_role_policy" "default" {
  name = "${var.environment}-service-${var.service_name}--dynamodb"

  role = var.role_name

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      for dynamodb_table_arn in var.dynamodb_table_arns : {
        "Effect" : "Allow",
        "Action" : ["dynamodb:*"],
        "Resource" : dynamodb_table_arn,
      }
    ]
  })
}
