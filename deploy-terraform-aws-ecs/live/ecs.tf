module "ecs_cluster" {
  source = "../modules/ecs-cluster"

  environment  = var.environment
  cluster_name = "transactional-outbox"
}

module "ecs_iam_task_execution_role" {
  source = "../modules/ecs-iam-task-execution-role"

  environment  = var.environment
  cluster_name = "transactional-outbox"
}
