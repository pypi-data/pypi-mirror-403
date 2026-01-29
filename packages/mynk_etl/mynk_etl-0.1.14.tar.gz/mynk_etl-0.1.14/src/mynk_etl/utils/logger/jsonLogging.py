"""JSON-formatted logging utilities.

Provides JSON log formatting and filtering capabilities for structured logging
with run ID, job type, and custom fields.
"""

import datetime as dt
import json
import logging
from mynk_etl.utils.common.constants import Constants

LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class logJSONFormatter(logging.Formatter):
    """Format log records as JSON strings with structured fields.

    Converts Python log records into JSON format with customizable field mapping,
    including run ID, job type, timestamp, and exception/stack information.
    """
    def __init__(
        self,
        *,
        fmt_keys: dict[str, str] | None = None,
    ):
        """Initialize JSON formatter.

        Args:
            fmt_keys (dict[str, str], optional): Mapping of JSON keys to log record attributes
        """
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}


    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string.

        Args:
            record (logging.LogRecord): The log record to format

        Returns:
            str: JSON-formatted log string
        """
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord):
        """Prepare log record as dictionary with all relevant fields.

        Args:
            record (logging.LogRecord): The log record to prepare

        Returns:
            dict: Dictionary containing all log fields with run ID, job type,
                  timestamp, and exception information if applicable
        """
        always_fields = {
            "run_id": Constants.RUN_ID.value,
            "jobtype": "pyStream",
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(
                record.created, tz=None
            ).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: msg_val
            if (msg_val := always_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val
        
        return message


class NonErrorFilter(logging.Filter):
    """Filter that passes only non-error level log records.

    Used to separate error-level logs from standard output logging.
    """

    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        """Filter log record based on log level.

        Args:
            record (logging.LogRecord): The log record to filter

        Returns:
            bool: True if log level is INFO or lower, False otherwise
        """
        return record.levelno <= logging.INFO