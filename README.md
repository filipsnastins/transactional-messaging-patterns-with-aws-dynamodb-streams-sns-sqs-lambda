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
    "customer_id": "b15658af-1643-4e59-b709-bb970b3a8f08",
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
