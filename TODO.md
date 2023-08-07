# TODOs

## Customers

- [x] Domain logic
- [x] Use cases
- [ ] Don't inherit from Protocols
- [ ] Hypermedia links should include full URL with protocol and host

## Orders

## Inbox

- [ ] Inbox table - making consumers idempotent
  - Order Created, Order Released, Order Created (received again)

## Outbox

- [x] DynamoDB Streams on event store table (outbox)
- [x] Separate DynamoDB tables for aggregate store and event store (outbox)
- [ ] Move generic UOW and Repository code to a library
- [ ] Configurable aggregate ID on the outbox table (customer_id, order_id) with GSI
- [ ] Correlation ID with GSI

## Tests

- [x] Configure CI pipeline with GitHub Actions for testing service-customers and service-order independently
- [x] End-to-end tests for service-customers

## Deploy

- [x] Deploy service-customers to ECS
- [x] Deploy service-orders to ECS
