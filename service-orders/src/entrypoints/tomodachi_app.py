import contextlib
import uuid

import tomodachi
from aiohttp import web
from stockholm import Money
from tomodachi.envelope.json_base import JsonBase
from tomodachi_bootstrap import TomodachiServiceBase
from transactional_messaging.idempotent_consumer import MessageAlreadyProcessedError

from adapters import dynamodb, inbox, outbox, sns
from orders.commands import ApproveOrderCommand, CancelOrderCommand, CreateOrderCommand, RejectOrderCommand
from service_layer import use_cases, views
from service_layer.response import ResponseTypes
from service_layer.unit_of_work import DynamoDBUnitOfWork

STATUS_CODES: dict[ResponseTypes, int] = {
    ResponseTypes.SUCCESS: 200,
    ResponseTypes.ORDER_NOT_FOUND_ERROR: 404,
    ResponseTypes.ORDER_ALREADY_EXISTS_ERROR: 400,
    ResponseTypes.PENDING_ORDER_CANNOT_BE_CANCELLED_ERROR: 400,
    ResponseTypes.SYSTEM_ERROR: 500,
}


class TomodachiService(TomodachiServiceBase):
    name = "service-orders"

    async def _start_service(self) -> None:
        if self.is_dev_env:
            await sns.create_topics()
            await dynamodb.create_orders_table()
            await inbox.create_inbox_table()
            await outbox.create_outbox_table()
            await outbox.create_dynamodb_streams_outbox()

    @tomodachi.http("GET", r"/orders/health/?", ignore_logging=[200])
    async def healthcheck(self, request: web.Request, correlation_id: uuid.UUID) -> web.Response:
        return web.json_response({"status": "ok"}, status=200)

    @tomodachi.http_error(status_code=500)
    async def error_500(self, request: web.Request, correlation_id: uuid.UUID) -> web.Response:
        return web.json_response({"error": ResponseTypes.SYSTEM_ERROR.value}, status=500)

    @tomodachi.http("POST", r"/orders")
    async def create_order_handler(self, request: web.Request, correlation_id: uuid.UUID) -> web.Response:
        async with DynamoDBUnitOfWork() as uow:
            data = await request.json()
            cmd = CreateOrderCommand(
                correlation_id=correlation_id,
                customer_id=uuid.UUID(data["customer_id"]),
                order_total=Money.from_sub_units(int(data["order_total"])).as_decimal(),
            )
            response = await use_cases.create_order(uow, cmd)
            return web.json_response(response.to_dict(), status=STATUS_CODES[response.type])

    @tomodachi.http("GET", r"/order/(?P<order_id>[^/]+?)/?")
    async def get_order_handler(self, request: web.Request, order_id: str, correlation_id: uuid.UUID) -> web.Response:
        async with DynamoDBUnitOfWork() as uow:
            response = await views.get_order(uow, order_id=uuid.UUID(order_id))
            return web.json_response(response.to_dict(), status=STATUS_CODES[response.type])

    @tomodachi.http("POST", r"/order/(?P<order_id>[^/]+?)/cancel?")
    async def cancel_order_handler(
        self, request: web.Request, order_id: str, correlation_id: uuid.UUID
    ) -> web.Response:
        async with DynamoDBUnitOfWork() as uow:
            cmd = CancelOrderCommand(correlation_id=correlation_id, order_id=uuid.UUID(order_id))
            response = await use_cases.cancel_order(uow, cmd)
            return web.json_response(response.to_dict(), status=STATUS_CODES[response.type])

    @tomodachi.aws_sns_sqs(
        "customer--credit-reserved",
        queue_name="order--customer-credit-reserved",
        dead_letter_queue_name="order--customer-credit-reserved--dlq",
        max_receive_count=3,
        message_envelope=JsonBase,
    )
    async def customer_credit_reserved_handler(self, data: dict, correlation_id: uuid.UUID) -> None:
        with contextlib.suppress(MessageAlreadyProcessedError):
            async with DynamoDBUnitOfWork(message_id=uuid.UUID(data["event_id"])) as uow:
                cmd = ApproveOrderCommand(correlation_id=correlation_id, order_id=uuid.UUID(data["order_id"]))
                await use_cases.approve_order(uow, cmd)

    @tomodachi.aws_sns_sqs(
        "customer--credit-reservation-failed",
        queue_name="order--customer-credit-reservation-failed",
        dead_letter_queue_name="order--customer-credit-reservation-failed--dlq",
        max_receive_count=3,
        message_envelope=JsonBase,
    )
    async def customer_credit_reservation_failed_handler(self, data: dict, correlation_id: uuid.UUID) -> None:
        with contextlib.suppress(MessageAlreadyProcessedError):
            async with DynamoDBUnitOfWork(message_id=uuid.UUID(data["event_id"])) as uow:
                cmd = RejectOrderCommand(correlation_id=correlation_id, order_id=uuid.UUID(data["order_id"]))
                await use_cases.reject_order(uow, cmd)

    @tomodachi.aws_sns_sqs(
        "customer--validation-failed",
        queue_name="order--customer-validation-failed",
        dead_letter_queue_name="order--customer-validation-failed--dlq",
        max_receive_count=3,
        message_envelope=JsonBase,
    )
    async def customer_validation_failed_handler(self, data: dict, correlation_id: uuid.UUID) -> None:
        with contextlib.suppress(MessageAlreadyProcessedError):
            async with DynamoDBUnitOfWork(message_id=uuid.UUID(data["event_id"])) as uow:
                cmd = RejectOrderCommand(correlation_id=correlation_id, order_id=uuid.UUID(data["order_id"]))
                await use_cases.reject_order(uow, cmd)
