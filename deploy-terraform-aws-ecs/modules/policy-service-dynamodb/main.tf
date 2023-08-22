resource "aws_iam_role_policy" "default" {
  name = "policy-${var.environment}-service-${var.service_name}--dynamodb"

  role = var.role_name

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:ConditionCheckItem",
          "dynamodb:DeleteItem",
          "dynamodb:DescribeLimits",
          "dynamodb:DescribeStream",
          "dynamodb:DescribeTable",
          "dynamodb:GetItem",
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:ListStreams",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem",
        ],
        "Resource" : flatten(
          [
            for dynamodb_table_arn in var.dynamodb_table_arns : [
              dynamodb_table_arn,
              "${dynamodb_table_arn}/index/*",
              "${dynamodb_table_arn}/stream/*"
            ]
          ]
        )
      }
    ]
  })
}
