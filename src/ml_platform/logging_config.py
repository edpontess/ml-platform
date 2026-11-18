import json
import logging
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "event"):
            log_record["event"] = record.event

        if hasattr(record, "method"):
            log_record["method"] = record.method

        if hasattr(record, "path"):
            log_record["path"] = record.path

        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code

        if hasattr(record, "duration_ms"):
            log_record["duration_ms"] = record.duration_ms

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logger = logging.getLogger("ml_platform")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
