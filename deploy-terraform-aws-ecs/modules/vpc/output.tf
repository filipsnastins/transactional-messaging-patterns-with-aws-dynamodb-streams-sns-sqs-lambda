output "id" {
  value = aws_default_vpc.default.id
}

output "subnet_ids" {
  value = [
    aws_default_subnet.subnet_a.id,
    aws_default_subnet.subnet_b.id,
    aws_default_subnet.subnet_c.id,
  ]
}
