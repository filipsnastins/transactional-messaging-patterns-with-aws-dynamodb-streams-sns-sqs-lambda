# Deploying to AWS Elastic Container Service (ECS) with Terraform

- Application stack:

  - TODO - describe application components

- Create AWS resources

```bash
terraform init
terraform apply
```

- Build and push Docker image to AWS Elastic Container Registry (ECR)

```bash
docker build -t test-45d8-tomodachi-transactional-outbox-service-customers --platform=linux/amd64 .
docker tag test-45d8-tomodachi-transactional-outbox-service-customers:latest 758308814218.dkr.ecr.eu-west-1.amazonaws.com/test-45d8-tomodachi-transactional-outbox-service-customers:latest
docker push 758308814218.dkr.ecr.eu-west-1.amazonaws.com/test-45d8-tomodachi-transactional-outbox-service-customers:latest

docker build -t test-45d8-tomodachi-transactional-outbox-service-orders --platform=linux/amd64 .
docker tag test-45d8-tomodachi-transactional-outbox-service-orders:latest 758308814218.dkr.ecr.eu-west-1.amazonaws.com/test-45d8-tomodachi-transactional-outbox-service-orders:latest
docker push 758308814218.dkr.ecr.eu-west-1.amazonaws.com/test-45d8-tomodachi-transactional-outbox-service-orders:latest
```

## References

- [How to Deploy a Dockerised Application on AWS ECS With Terraform](https://medium.com/p/3e6bceb48785)
