module "ecs_cluster" {
  source = "../modules/ecs-cluster"

  environment  = var.environment
  cluster_name = "transactional-outbox"
}

module "ecs_iam_policy" {
  source = "../modules/ecs-iam-policy"
}
