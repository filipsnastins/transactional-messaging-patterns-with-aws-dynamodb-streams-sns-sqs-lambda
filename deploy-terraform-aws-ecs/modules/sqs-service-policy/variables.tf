variable "environment" {
  type = string
}

variable "service_name" {
  type = string
}

variable "role_name" {
  type = string
}

variable "sqs_queue_arns" {
  type = list(string)
}
