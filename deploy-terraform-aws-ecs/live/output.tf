output "alb_ingress_url" {
  value = "http://${module.alb.dns_name}"
}

output "service_orders_healthcheck_url" {
  value = "http://${module.alb.dns_name}/orders/health"
}

output "service_customers_healthcheck_url" {
  value = "http://${module.alb.dns_name}/customers/health"
}
