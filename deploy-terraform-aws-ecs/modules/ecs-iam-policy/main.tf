module "ecs_assume_role_policy" {
  source = "../ecs-assume-role-policy"
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

    resources = [
      "arn:aws:logs:*:*:*"
    ]
  }
}

resource "aws_iam_policy" "ecsCloudWatchLogs_policy" {
  name   = "ecsCloudWatchLogs"
  policy = data.aws_iam_policy_document.ecsCloudWatchLogs_policy.json
}

resource "aws_iam_role" "ecsTaskExecutionRole" {
  name               = "ecsTaskExecutionRole"
  assume_role_policy = module.ecs_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_policy" {
  role       = aws_iam_role.ecsTaskExecutionRole.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole__ecsCloudWatchLogs_policy" {
  role       = aws_iam_role.ecsTaskExecutionRole.name
  policy_arn = aws_iam_policy.ecsCloudWatchLogs_policy.arn
}
