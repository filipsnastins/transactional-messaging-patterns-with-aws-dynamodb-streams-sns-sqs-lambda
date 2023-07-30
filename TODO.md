# TODOs

## Customers

- [x] Domain logic
- [ ] Use cases
- [ ] Don't inherit from Protocols
- [ ] Hypermedia links should include full URL with protocol and host

## Inbox

- [ ] Inbox table - making consumers idempotent
  - Order Created, Order Released, Order Created (received twice)

## Outbox

- [ ] DynamoDB Streams on event store table (outbox)
- [x] Separate DynamoDB tables for aggregate store and event store (outbox)
- [ ] Move generic UOW and Repository code to a library

## Tests

- [x] Configure CI pipeline with GitHub Actions for testing service-customers and service-order independently
- [x] End-to-end tests for service-customers

## Deploy

- [x] Deploy service-customers to ECS
- [ ] Deploy service-orders to ECS
