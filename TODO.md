# TODOs

## Documentation

- [ ] AWS architecture diagram
- [ ] Simple transactional outbox and idempotent consumer diagram
- [ ] Prose description

## service-customers

✅

## service-orders

✅

## service-order-history

- [ ] Feature specs

## Inbox

✅

## Outbox

- [ ] Tomodachi SQS consumer doesn't work when SQS encryption is enabled by Terraform?
- [ ] Increase ApproximateDispatchCount when marking a message as dispatched
- [ ] A script to manually publish not dispatched messages
- [ ] How to resend DynamoDB Streams Iterator from DLQ to the Outbox Lambda?
- [ ] CloudWatch alarm: NotDispatchedMessagesIndex - Lambda that's periodically checking for old, not dispatched messages
- [ ] CloudWatch alarm: use Amazon CloudWatch on IteratorAge to determine if your Kinesis stream is being processed. For example, configure a CloudWatch alarm with a maximum setting to 30000 (30 seconds).

## Unit of Work

✅

## Lambda

✅

## Tests

- [ ] End-to-end tests - deploy to AWS autotest environment with Terratest and perform basic sanity checks
- [ ] End-to-end tests - deploy local Docker Compose stack with Testcontainers and perform basic sanity checks

## Deploy

- [ ] GitHub Actions workflows for monorepo
