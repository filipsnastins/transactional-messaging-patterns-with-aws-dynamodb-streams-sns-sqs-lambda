def lambda_handler(event: dict, context: dict) -> None:
    print(event, flush=True)
    print(context, flush=True)
