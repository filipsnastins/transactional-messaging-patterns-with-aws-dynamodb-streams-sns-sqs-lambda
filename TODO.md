# TODOs

## service-customers

✅

## service-orders

✅

## service-order-history

- [ ] Feature specs

## Inbox

✅

## Outbox

✅

## Unit of Work

✅

## Lambda

- [ ] Production-ready outbox Lambda
- [ ] Marks messages as dispatched
  - Mind infinite loop
- [ ] CloudWatch alarm on NotDispatchedMessagesIndex - scheduled lambda that's periodically checking for not dispatched messages?

## Tests

- [ ] End-to-end tests

## Deploy

- [ ] Production-ready Terraform modules for deployment to ECS
  - Deploy container
  - Deploy outbox Lambda
  - Create DynamoDB table
  - Create topics and queues (SNS SQS)
- [ ] Test Terraform modules with Terratest
- [ ] GitHub Actions workflows
