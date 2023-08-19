# tfsec:ignore:aws-elb-alb-not-public
# tfsec:ignore:aws-elb-http-not-used
# tfsec:ignore:aws-ec2-no-public-egress-sgr
module "alb" {
  source = "../modules/alb"

  environment = var.environment
  name        = "transactional-outbox"
  subnet_ids  = module.vpc.subnet_ids
}
