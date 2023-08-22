variable "environment" {
  type = string
}

variable "service_name" {
  type = string
}

variable "dynamodb_table_arns" {
  type = list(string)
}

variable "sns_topic_arns" {
  type = list(string)
}

variable "sqs_queue_arns" {
  type = list(string)
}
