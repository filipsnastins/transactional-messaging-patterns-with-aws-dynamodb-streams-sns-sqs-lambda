# lambda-outbox-dynamodb-streams

## Build Lambda `zip` package for local testing

```bash
poetry install --with lambda

poetry shell

poetry export --with lambda -f requirements.txt --output src/lambda_outbox_dynamodb_streams/requirements.txt

rm -rf package
mkdir package
cp -R src/lambda_outbox_dynamodb_streams/* package
cd package
pip install -r requirements.txt -t .
rm -rf ../src/lambda_outbox_dynamodb_streams/lambda_outbox_dynamodb_streams.zip
zip -r ../src/lambda_outbox_dynamodb_streams/lambda_outbox_dynamodb_streams.zip .
cd ..
rm -rf package
```
