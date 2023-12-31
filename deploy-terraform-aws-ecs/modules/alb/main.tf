# tfsec:ignore:aws-elb-alb-not-public
resource "aws_security_group" "alb_security_group" {
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # tfsec:ignore:aws-ec2-no-public-ingress-sgr
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "service_security_group" {
  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.alb_security_group.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_alb" "default" {
  name               = "${var.environment}-${var.name}"
  load_balancer_type = "application"

  subnets         = var.subnet_ids
  security_groups = [aws_security_group.alb_security_group.id]

  drop_invalid_header_fields = true
}

resource "aws_lb_listener" "default" {
  load_balancer_arn = aws_alb.default.arn
  port              = "80"
  protocol          = "HTTP" # tfsec:ignore:aws-elb-http-not-used

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      status_code  = "404"
      message_body = "Not Found"
    }
  }
}
