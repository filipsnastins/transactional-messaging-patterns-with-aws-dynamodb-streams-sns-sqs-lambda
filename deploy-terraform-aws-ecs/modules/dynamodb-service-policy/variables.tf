variable "environment" {
  type = string
}

variable "service_name" {
  type = string
}

variable "role_name" {
  type = string
}

variable "dynamodb_table_arns" {
  type = list(string)
}
