variable "function_name" {
  type = string
}

variable "dynamodb_table_arn" {
  type = string
}

variable "dynamodb_table_stream_arn" {
  type = string
}

variable "sns_topic_arns" {
  type = list(string)
}

variable "sqs_queue_arns" {
  type = list(string)
}
