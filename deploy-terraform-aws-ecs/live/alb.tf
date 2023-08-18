module "alb" {
  source = "../modules/alb"

  region      = var.region
  environment = var.environment
  name        = "transactional-outbox"
  subnet_ids  = module.vpc.subnet_ids
}
