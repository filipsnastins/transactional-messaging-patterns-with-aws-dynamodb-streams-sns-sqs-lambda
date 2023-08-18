output "name" {
  value = aws_dynamodb_table.default.name
}

output "stream_arn" {
  value = aws_dynamodb_table.default.stream_arn
}
