resource "aws_dynamodb_table" "default" {
  name         = "${var.environment}-${var.aggregate_name}-inbox"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "PK"

  attribute {
    name = "PK"
    type = "S"
  }
}
