output "name" {
  value = aws_dynamodb_table.default.name
}

output "arn" {
  value = aws_dynamodb_table.default.arn
}

output "stream_arn" {
  value = aws_dynamodb_table.default.stream_arn
}
