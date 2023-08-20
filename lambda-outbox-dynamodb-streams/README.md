# lambda-outbox-dynamodb-streams

## Build Lambda `zip` package

```bash
docker buildx build --platform linux/arm64 -f Dockerfile.package --target=package --output type=local,dest=$(pwd)/src/lambda_outbox_dynamodb_streams ..

docker buildx build --platform linux/amd64 -f Dockerfile.package --target=package --output type=local,dest=$(pwd)/src/lambda_outbox_dynamodb_streams ..
```
