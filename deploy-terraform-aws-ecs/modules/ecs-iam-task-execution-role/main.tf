module "ecs_assume_role_policy" {
  source = "../ecs-assume-role-policy"
}

resource "aws_iam_role" "default" {
  name               = "${var.environment}-${var.cluster_name}-ecsTaskExecutionRole"
  assume_role_policy = module.ecs_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "attach_ecsTaskExecutionRole_policy" {
  role       = aws_iam_role.default.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ecsCloudWatchLogs_policy" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]

    # tfsec:ignore:aws-iam-no-policy-wildcards
    resources = [
      "arn:aws:logs:*:*:*"
    ]
  }
}

resource "aws_iam_policy" "ecsCloudWatchLogs_policy" {
  name   = "ecsCloudWatchLogs"
  policy = data.aws_iam_policy_document.ecsCloudWatchLogs_policy.json
}

resource "aws_iam_role_policy_attachment" "attach_ecsCloudWatchLogs_policy" {
  role       = aws_iam_role.default.name
  policy_arn = aws_iam_policy.ecsCloudWatchLogs_policy.arn
}
