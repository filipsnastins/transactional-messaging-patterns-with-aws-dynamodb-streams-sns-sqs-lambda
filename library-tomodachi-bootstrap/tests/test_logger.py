import json
import logging
import uuid

import pytest
import structlog

from tomodachi_bootstrap.logger import configure_structlog


def test_default_json_renderer(caplog: pytest.LogCaptureFixture) -> None:
    configure_structlog()
    structlog.configure(cache_logger_on_first_use=False)
    logger: structlog.stdlib.BoundLogger = structlog.get_logger()

    logger.info("test_log")

    assert len(caplog.record_tuples) == 1
    record = caplog.record_tuples[0]
    assert record[0] == "tests.test_logger"
    assert record[1] == logging.INFO
    payload = json.loads(record[2])
    assert payload == {
        "event": "test_log",
        "logger": "tests.test_logger",
        "level": "info",
        "timestamp": payload["timestamp"],
    }


def test_uuid_casted_to_string(caplog: pytest.LogCaptureFixture) -> None:
    configure_structlog()
    structlog.configure(cache_logger_on_first_use=False)
    logger: structlog.stdlib.BoundLogger = structlog.get_logger()
    correlation_id = uuid.UUID("430d1506-5e9c-467d-a303-751d2ddee79d")

    logger.info("test_log", correlation_id=correlation_id)

    assert len(caplog.record_tuples) == 1
    payload = json.loads(caplog.record_tuples[0][2])
    assert payload["correlation_id"] == "430d1506-5e9c-467d-a303-751d2ddee79d"
