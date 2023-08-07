FROM public.ecr.aws/lambda/python:3.10

COPY src/lambda_outbox_dynamodb_streams/requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

COPY src/lambda_outbox_dynamodb_streams/app ${LAMBDA_TASK_ROOT}

CMD ["app.lambda_function.lambda_handler"]
