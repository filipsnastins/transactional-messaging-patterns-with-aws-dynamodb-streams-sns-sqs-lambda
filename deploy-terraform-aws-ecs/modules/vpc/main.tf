resource "aws_default_vpc" "default" {
}

resource "aws_default_subnet" "subnet_a" {
  availability_zone = "${var.region}a"
}

resource "aws_default_subnet" "subnet_b" {
  availability_zone = "${var.region}b"
}

resource "aws_default_subnet" "subnet_c" {
  availability_zone = "${var.region}c"
}
