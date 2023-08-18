terraform {
  required_version = ">= 1.4.4"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_service_discovery_http_namespace" "default" {
  name = "${var.environment}-${var.cluster_name}"
}

resource "aws_ecs_cluster" "default" {
  name = "${var.environment}-${var.cluster_name}"

  service_connect_defaults {
    namespace = aws_service_discovery_http_namespace.default.arn
  }
}
