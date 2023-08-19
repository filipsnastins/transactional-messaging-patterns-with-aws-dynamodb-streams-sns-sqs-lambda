resource "aws_dynamodb_table" "default" {
  name         = "${var.environment}-${var.aggregate_name}-inbox"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "PK"

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  attribute {
    name = "PK"
    type = "S"
  }
}
