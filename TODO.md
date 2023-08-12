# TODOs

## Customers

...

## Orders

...

## service-order-history

- [ ] Feature specs

## Inbox

- [ ] Inbox table - making consumers idempotent
  - Order Created, Order Released, Order Created (received again)

## Outbox

- [ ] **Tests**

## Unit of Work

- [ ] Separate library? Decouple from `library-tomodachi-outbox`?

## Lambda

- [ ] Production-ready outbox Lambda
- [ ] Marks messages as dispatched
  - Mind infinite loop

## Tests

- [ ] End-to-end tests

## Deploy

- [ ] Production-ready Terraform modules for deployment to ECS
  - Deploy container
  - Deploy outbox Lambda
  - Create DynamoDB table
  - Create topics and queues (SNS SQS)
- [ ] Test Terraform modules with Terratest
