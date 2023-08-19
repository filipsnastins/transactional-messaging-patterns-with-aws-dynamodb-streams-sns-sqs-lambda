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

- [ ] Increase DispatchedCount when marking a message as dispatched

## Unit of Work

✅

## Lambda

...

## Tests

- [ ] End-to-end tests

## Deploy

- [x] Production-ready Terraform modules for deployment to ECS
  - Deploy containers
  - Deploy outbox lambda
  - Create DynamoDB tables
  - Create topics, queues and dead-letter-queues
- [x] Add DLQ for outbox lambda
- [ ] Refactor Terraform, explore [Lambda best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [ ] Test Lambda + DLQ - how to retry failed DynamoDB stream messages
- [ ] CloudWatch alarm on NotDispatchedMessagesIndex - scheduled lambda that's periodically checking for not dispatched messages
- [ ] GitHub Actions workflows
- [ ] Test Terraform modules with Terratest
