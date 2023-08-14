# TODOs

## Customers

...

## Orders

...

## service-order-history

- [ ] Feature specs

## Inbox

- [ ] Inbox table - idempotent consumer pattern
  - Order Created, Order Released, Order Created (received again)

## Outbox

...

## Unit of Work

...

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
