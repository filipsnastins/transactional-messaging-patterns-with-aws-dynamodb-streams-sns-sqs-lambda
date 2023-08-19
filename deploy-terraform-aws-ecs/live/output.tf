output "service_orders_url" {
  value = "http://${module.alb.dns_name}/orders/health"
}

output "service_customers_url" {
  value = "http://${module.alb.dns_name}/customers/health"
}
