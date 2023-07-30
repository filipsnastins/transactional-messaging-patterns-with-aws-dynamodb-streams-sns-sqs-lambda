resource "aws_ecr_repository" "service_customers" {
  name = "${var.environment}-tomodachi-transactional-outbox-service-customers"
}

resource "aws_ecr_repository" "service_orders" {
  name = "${var.environment}-tomodachi-transactional-outbox-service-orders"
}
