variable "environment" {
  type = string
}

variable "service_name" {
  type = string
}

variable "dynamodb_outbox_table_name" {
  type = string
}

variable "dynamodb_outbox_table_arn" {
  type = string
}

variable "dynamodb_outbox_table_stream_arn" {
  type = string
}

variable "create_sns_topics" {
  type = list(string)
}

variable "lambda_source_zip_path" {
  type    = string
  default = "../../lambda-outbox-dynamodb-streams/src/lambda_outbox_dynamodb_streams/lambda_outbox_dynamodb_streams_arm64.zip"
}

variable "architecture" {
  type    = string
  default = "arm64"
}

variable "batch_size" {
  type    = number
  default = 30
}

variable "maximum_retry_attempts" {
  type    = number
  default = 10
}

variable "parallelization_factor" {
  type    = number
  default = 1
}

variable "maximum_event_age_in_seconds" {
  type    = number
  default = 1800 # 30 minutes
}
