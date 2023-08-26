variable "function_name" {
  type = string
}

variable "role_name" {
  type = string
}

variable "sqs_queue_arns" {
  type = list(string)
}
