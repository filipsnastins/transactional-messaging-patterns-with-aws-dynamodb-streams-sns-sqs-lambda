resource "aws_iam_role_policy" "default" {
  name = "policy-${var.function_name}--xray"

  role = var.role_name

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : ["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
        "Resource" : "*",
      }
    ],
  })
}
