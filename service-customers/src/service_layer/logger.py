import logging
import sys
import uuid

import structlog
from structlog.types import EventDict


def cast_uuid_to_str(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    for key, value in event_dict.items():
        if isinstance(value, uuid.UUID):
            event_dict[key] = str(value)
    return event_dict


def configure_structlog(log_level: int = logging.INFO) -> None:
    processors = [
        structlog.contextvars.merge_contextvars,
        cast_uuid_to_str,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.ExceptionRenderer(),
        structlog.processors.ExceptionPrettyPrinter(),
        structlog.dev.ConsoleRenderer(),
    ]
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)
    structlog.configure(
        processors=processors,  # type: ignore
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
