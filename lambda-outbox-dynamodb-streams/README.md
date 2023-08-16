# lambda-outbox-dynamodb-streams

## Build Lambda `zip` package for local testing

```bash
docker buildx build -f Dockerfile.package --target=package --output type=local,dest=$(pwd)/src/lambda_outbox_dynamodb_streams ..
```
