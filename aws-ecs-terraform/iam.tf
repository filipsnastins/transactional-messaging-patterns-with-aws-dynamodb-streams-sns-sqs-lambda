data "aws_iam_policy_document" "assumeRole_ecsTasks_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy" "AmazonDynamoDBFullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

data "aws_iam_policy" "AmazonSNSFullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonSNSFullAccess"
}

data "aws_iam_policy" "AmazonSQSFullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}

# Services are given full access to DynamoDB, SNS and SQS
# In the real production environment, you should limit the access to only the resources that the service needs
# In this example full access is given for simplicity
resource "aws_iam_role" "ecsTaskRole" {
  name               = "${var.environment}-tomodachi-transactional-outbox--service"
  description        = "Role for ECS tasks - microservices running in Docker containers"
  assume_role_policy = data.aws_iam_policy_document.assumeRole_ecsTasks_policy.json
}

resource "aws_iam_role_policy_attachment" "ecsTaskRole__AmazonDynamoDBFullAccess" {
  role       = aws_iam_role.ecsTaskRole.name
  policy_arn = data.aws_iam_policy.AmazonDynamoDBFullAccess.arn
}

resource "aws_iam_role_policy_attachment" "ecsTaskRole__AmazonSNSFullAccess" {
  role       = aws_iam_role.ecsTaskRole.name
  policy_arn = data.aws_iam_policy.AmazonSNSFullAccess.arn
}

resource "aws_iam_role_policy_attachment" "ecsTaskRole__AmazonSQSFullAccess" {
  role       = aws_iam_role.ecsTaskRole.name
  policy_arn = data.aws_iam_policy.AmazonSQSFullAccess.arn
}
