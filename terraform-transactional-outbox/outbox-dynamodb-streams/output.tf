output "lambda_outbox_function_name" {
  value = aws_lambda_function.default
}

output "dynamodb_outbox_table_name" {
  value = module.dynamodb_outbox_table.name
}

output "dynamodb_outbox_table_arn" {
  value = module.dynamodb_outbox_table.arn
}
