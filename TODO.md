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

- [ ] Production-ready Terraform modules for deployment to ECS
  - Deploy containers
  - Deploy outbox lambda
  - Create DynamoDB tables
  - Create topics, queues and dead-letter-queues
- [ ] Add DLQ for outbox lambda
- [ ] GitHub Actions workflows
- [ ] Test Terraform modules with Terratest
- [ ] CloudWatch alarm on NotDispatchedMessagesIndex - scheduled lambda that's periodically checking for not dispatched messages
