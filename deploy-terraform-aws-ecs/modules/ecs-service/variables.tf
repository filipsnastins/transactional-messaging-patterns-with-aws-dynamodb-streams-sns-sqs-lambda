variable "region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type = string
}

variable "service_name" {
  type = string
}

variable "port" {
  type = number
}

variable "vpc_id" {
  type = string
}

variable "vpc_subnet_ids" {
  type = list(string)
}

variable "alb_listener_arn" {
  type = string
}

variable "security_group_id" {
  type = string
}

variable "ecs_cluster_id" {
  type = string
}

variable "ecs_task_execution_role_arn" {
  type = string
}

variable "memory" {
  type = number
}

variable "cpu" {
  type = number
}

variable "replicas" {
  type = number
}

variable "http_healthcheck_path" {
  type = string
}

variable "http_listen_path_pattern" {
  type = string
}

variable "environment_variables" {
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}
