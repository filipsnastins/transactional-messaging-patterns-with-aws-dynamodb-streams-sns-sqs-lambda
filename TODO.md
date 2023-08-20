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
- [ ] CloudWatch alarm: NotDispatchedMessagesIndex - Lambda that's periodically checking for old, not dispatched messages
- [ ] CloudWatch alarm: use Amazon CloudWatch on IteratorAge to determine if your Kinesis stream is being processed. For example, configure a CloudWatch alarm with a maximum setting to 30000 (30 seconds).
- [ ] How to resend DynamoDB Streams Iterator from DLQ to the Outbox Lambda?
- [ ] A script to resend stuck, not dispatched messages.
  - Invoke Lambda manually with simulated/manually assembled DynamoDB Streams event?
- [ ] A script to manually re-publish already dispatched messages
  - `OutboxRepository.mark_for_dispatch`
    - [ ] Set `IsDispatched` to `false`, and let Lambda pickup `MODIFY` even and capture `OLD_IMAGE IsDispatched=true` and `NEW_IMAGE IsDispatched=false`; resend message automatically
    - [ ] Add `NotDispatched=Y`
    - [x] Rename `DispatchedAt` to `LastDispatchedAt`

## Unit of Work

✅

## Lambda Outbox DynamoDB Streams

✅

## Tests

- [ ] End-to-end tests - deploy to AWS autotest environment with Terratest and perform basic sanity checks
- [ ] End-to-end tests - deploy local Docker Compose stack with Testcontainers and perform basic sanity checks

## Deploy

- [ ] GitHub Actions workflows for monorepo
