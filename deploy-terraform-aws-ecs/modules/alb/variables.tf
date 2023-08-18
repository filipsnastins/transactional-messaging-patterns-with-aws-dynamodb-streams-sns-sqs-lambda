variable "region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type = string
}

variable "name" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}
