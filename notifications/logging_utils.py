import json
import logging
import traceback
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """
    Formats every log record as a single JSON line.
    This makes logs parseable by tools like Datadog, Grafana Loki,
    CloudWatch, and any ELK stack without custom parsers.

    Every line contains at minimum:
        timestamp, level, logger, message, environment
    On exceptions it adds:
        exception_type, exception_message, traceback
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp':   datetime.now(timezone.utc).isoformat(),
            'level':       record.levelname,
            'logger':      record.name,
            'message':     record.getMessage(),
            'environment': _get_env(),
        }

        # Copy any extra fields attached via logger.info('...', extra={...})
        for key, val in record.__dict__.items():
            if key not in _STDLIB_KEYS and not key.startswith('_'):
                try:
                    json.dumps(val)   # only include JSON-serialisable extras
                    payload[key] = val
                except (TypeError, ValueError):
                    payload[key] = str(val)

        # Exception info
        if record.exc_info:
            exc_type, exc_val, exc_tb = record.exc_info
            payload['exception_type']    = exc_type.__name__ if exc_type else None
            payload['exception_message'] = str(exc_val)
            payload['traceback']         = traceback.format_exception(exc_type, exc_val, exc_tb)

        return json.dumps(payload, ensure_ascii=False)


def _get_env() -> str:
    from django.conf import settings
    return getattr(settings, 'ENVIRONMENT', 'development')


# Standard LogRecord attributes we don't want to echo into JSON
_STDLIB_KEYS = frozenset({
    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
    'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
    'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
    'thread', 'threadName', 'processName', 'process', 'message',
    'taskName',
})