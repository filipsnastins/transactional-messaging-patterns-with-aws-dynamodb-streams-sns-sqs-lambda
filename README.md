# tomodachi-transactional-outbox

## Run locally with Docker Compose

- Start applications

```bash
docker compose up
```

- Get outbox lambda logs

```bash
awslocal --region=us-east-1 logs describe-log-groups

awslocal --region=us-east-1 logs tail /aws/lambda/lambda-dynamodb-streams--customers-outbox
awslocal --region=us-east-1 logs tail /aws/lambda/lambda-dynamodb-streams--orders-outbox
```

- Check DynamoDB content with [DynamoDB Admin](https://github.com/aaronshaf/dynamodb-admin) at `http://localhost:8001`

## Sample requests

- Create customer

  ```bash
  curl -X POST --header "Content-Type: application/json" -d '{
    "name": "Jane Doe",
    "credit_limit": 250
  }' http://localhost:9701/customers
  ```

- Create order

  ```bash
  curl -X POST --header "Content-Type: application/json" -d '{
    "customer_id": "56ec0470-0339-4004-9c99-42caadf5a076",
    "order_total": 100
  }' http://localhost:9702/orders
  ```

- Get customer

  ```bash
  curl http://localhost:9701/customer/15883bbb-dbf9-4ea0-afec-b2fab1a0ab2f
  ```

- Get order

  ```bash
  curl http://localhost:9702/order/a5ecbfba-32cd-4c94-bfcf-f6a4a8f8a91c
  ```

- Cancel order

  ```bash
  curl -X POST http://localhost:9702/order/a5ecbfba-32cd-4c94-bfcf-f6a4a8f8a91c/cancel
  ```

## Limitations

- To save storage costs, Inbox and Outbox repositories should use `DynamoDB time-to-live`
  to cleanup old items, for example, after one year.
- If a published message payload exceeds DynamoDB item size limit of `400 KB`, message saving to the database will fail.
  If large messages are expected, consider saving them in S3 and storing only a reference to the message in DynamoDB.
  Read more in [Best practices for storing large items and attributes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-use-s3-too.html).
  The same bottleneck will occur in SQS too, so the same approach for transporting large SQS messages needs to be implemented.
  Read more in [Managing large Amazon SQS messages using Amazon S3](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-s3-messages.html)

## Notes on running Outbox Lambda in a local environment or autotests

### Moto: `arm64` vs `amd64` Lambda architecture

Seems that Moto ignores specified Lambda architecture name, and uses whichever `mlupin/docker-lambda` Docker image
is pulled to the local Docker daemon. If you get errors that outbox messages are not dispatched, try to
delete locally cached `mlupin/docker-lambda` images and pull them again for your machines architecture.

No such problems observed with LocalStack.

### Moto: marking messages as dispatched doesn't work with Moto

When Outbox Lambda is trying to mark a message as dispatched, Lambda goes into an infinite loop.
That's why marking messages as dispatched is disabled when running Outbox Lambda in local environment or autotests.

Seems that it happens because Moto publishes DynamoDB stream message before it returns a successful response on
DynamoDB `put_item` operation, but further debugging in Moto is required.

No such problems observed with LocalStack.

## Resources and acknowledgements

- Application example and domain problem:
  - [github.com/eventuate-tram/eventuate-tram-examples-customers-and-orders](https://github.com/eventuate-tram/eventuate-tram-examples-customers-and-orders)
- Application design inspiration:
  - [github.com/cosmicpython/code](https://github.com/cosmicpython/code)
  - [github.com/pycabook/rentomatic](https://github.com/pycabook/rentomatic)
- Transactional messaging implementation inspiration:
  - [github.com/eventuate-tram/eventuate-tram-core](https://github.com/eventuate-tram/eventuate-tram-core)
- Books:
  - [Microservices Patterns: With Examples in Java.](https://microservices.io/book) Book by Chris Richardson.
  - [Architecture Patterns with Python: Enabling Test-Driven Development, Domain-Driven Design, and Event-Driven Microservices](https://www.cosmicpython.com/) Book by Harry Percival and Bob Gregory.
  - [Clean Architectures in Python: A practical approach to better software design.](https://leanpub.com/clean-architectures-in-python) Book by Leonardo Giordani.
- Articles:
  - ...

## Development

```bash
brew install tflint
brew install tfsec

# Run commit hooks
brew install pre-commit
pre-commit install

pre-commit run --all-files
```
