# tfsec:ignore:aws-ec2-no-default-vpc
module "vpc" {
  source = "../modules/vpc"

  region = var.region
}
