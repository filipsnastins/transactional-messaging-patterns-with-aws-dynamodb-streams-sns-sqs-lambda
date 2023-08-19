variable "environment" {
  type = string
}

variable "service_name" {
  type = string
}

variable "role_name" {
  type = string
}

variable "sns_topic_arns" {
  type = list(string)
}
