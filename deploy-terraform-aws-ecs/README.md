# deploy-terraform-aws-ecs

## Deploying Customers and Orders to AWS Elastic Container Service (ECS) with Terraform

- Application stack:

  - Containers deployed to AWS Elastic Container Service (ECS)
  - Docker images stored in private AWS Elastic Container Registry (ECR)
  - Ingress traffic via AWS Application Load Balancer (ALB) with path based routing
    - `/customer*` -> customers service
    - `/order*` -> orders service

- Create AWS resources

```bash
terraform init
terraform apply
```

- Build and push Docker images to AWS Elastic Container Registry (ECR)

```bash
export ECR_HOST=758308814218.dkr.ecr.us-east-1.amazonaws.com # Insert your ECR host here
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_HOST

export CUSTOMERS_IMAGE=test-45d8-service-customers:latest
docker build -t $CUSTOMERS_IMAGE --platform=linux/amd64 -f ../service-customers/Dockerfile ..
docker tag $CUSTOMERS_IMAGE $ECR_HOST/$CUSTOMERS_IMAGE
docker push $ECR_HOST/$CUSTOMERS_IMAGE

export ORDERS_IMAGE=test-45d8-service-orders:latest
docker build -t $ORDERS_IMAGE --platform=linux/amd64 -f ../service-orders/Dockerfile ..
docker tag $ORDERS_IMAGE $ECR_HOST/$ORDERS_IMAGE
docker push $ECR_HOST/$ORDERS_IMAGE
```

- Get service ingress URLs

```bash
terraform output
```

## References

- [How to Deploy a Dockerised Application on AWS ECS With Terraform](https://medium.com/p/3e6bceb48785)
