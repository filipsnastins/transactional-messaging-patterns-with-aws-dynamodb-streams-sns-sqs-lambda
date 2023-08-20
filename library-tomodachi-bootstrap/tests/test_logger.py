import json
import logging

import pytest
import structlog

from tomodachi_bootstrap.logger import configure_structlog


def test_default_json_renderer(caplog: pytest.LogCaptureFixture) -> None:
    configure_structlog()
    structlog.configure(cache_logger_on_first_use=False)
    logger: structlog.stdlib.BoundLogger = structlog.get_logger()

    logger.info("test_log")

    assert caplog.record_tuples
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
