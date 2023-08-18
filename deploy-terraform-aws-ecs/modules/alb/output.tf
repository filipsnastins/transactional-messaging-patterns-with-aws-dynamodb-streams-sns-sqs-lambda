output "id" {
  value = aws_alb.default.id
}

output "dns_name" {
  value = aws_alb.default.dns_name
}

output "service_security_group_id" {
  value = aws_security_group.service_security_group.id
}

output "listener_arn" {
  value = aws_lb_listener.default.arn
}
