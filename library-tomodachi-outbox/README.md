# library-tomodachi-transactional-outbox

- Get Lambda logs from LocalStack

```bash
awslocal --endpoint-url=http://localhost:55852 --region=us-east-1 logs tail /aws/lambda/lambda-dynamodb-streams--outbox

awslocal --endpoint-url=http://localhost:55852 --region=us-east-1 logs describe-log-groups

awslocal --endpoint-url=http://localhost:55852 --region=us-east-1 dynamodb list-tables

awslocal --endpoint-url=http://localhost:55852 --region=us-east-1 lambda list-functions
```

- Example of a DynamoDB Stream Record

```python
{
    "aws_region": "us-east-1",
    "dynamodb": {
        "approximate_creation_date_time": 1691214861,
        "keys": {"PK": "MESSAGE#7c436e55-f008-41f2-a72b-e692357050b4"},
        "new_image": {
            "PK": "MESSAGE#7c436e55-f008-41f2-a72b-e692357050b4",
            "MessageId": "7c436e55-f008-41f2-a72b-e692357050b4",
            "AggregateId": "45b9ee48-e3d7-42a4-946d-97a97b69ca9c",
            "CorrelationId": "844a6ada-25a4-4ffb-a4fb-d4cb91138e1f",
            "Topic": "test-topic",
            "Message": '{"message": "test-message"}',
            "CreatedAt": "2023-08-05T05:54:00.074033+00:00",
        },
        "old_image": None,
        "raw_event": "[SENSITIVE]",
        "sequence_number": "49643302929414334783348646724521516147482876163133538306",
        "size_bytes": 386,
        "stream_view_type": " <StreamViewType.NEW_AND_OLD_IMAGES: 3>",
    },
    "event_id": "c3ac1575",
    "event_name": " <DynamoDBRecordEventName.INSERT: 0>",
    "event_source": "aws:dynamodb",
    "event_source_arn": "arn:aws:dynamodb:us-east-1:000000000000:table/outbox/stream/2023-08-05T05:54:02.544",
    "event_version": "1.0",
    "raw_event": "[SENSITIVE]",
    "user_identity": None,
}
```

- <https://github.com/mLupine/docker-lambda/issues/22>

```bash
docker pull mlupin/docker-lambda:python3.10-arm64-202304201629
docker tag mlupin/docker-lambda:python3.10-arm64-202304201629 mlupin/docker-lambda:python3.10

docker pull mlupin/docker-lambda:python3.11-arm64-202304201629
docker tag mlupin/docker-lambda:python3.11-arm64-202304201629 mlupin/docker-lambda:python3.11
```
