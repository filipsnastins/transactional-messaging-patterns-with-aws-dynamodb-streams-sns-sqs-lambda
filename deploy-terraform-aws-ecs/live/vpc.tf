module "vpc" { # tfsec:ignore:aws-ec2-no-default-vpc
  source = "../modules/vpc"

  region = var.region
}
