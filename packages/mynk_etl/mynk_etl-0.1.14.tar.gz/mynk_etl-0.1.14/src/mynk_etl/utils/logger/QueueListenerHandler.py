"""Queue-based logging handler with listener support.

Provides a queue-based logging handler that asynchronously processes log records
using a QueueListener for improved logging performance.
"""

from logging.config import ConvertingList
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from atexit import register


def _resolve_handlers(lst: ConvertingList):
    """Resolve converting list to list of handlers.

    Args:
        lst (ConvertingList): Potentially lazy-loaded list of handlers

    Returns:
        list: List of fully resolved handler objects
    """
    if not isinstance(lst, ConvertingList):
        return lst

    # Indexing the list performs the evaluation.
    return [lst[i] for i in range(len(lst))]


class QueueListenerHandler(QueueHandler):
    """Queue-based handler with listener for asynchronous log processing.

    Extends QueueHandler to add a QueueListener that processes logs asynchronously,
    improving performance by moving I/O operations off the main thread.
    """

    def __init__(self, handlers, respect_handler_level=True, auto_run=True, queue=Queue(-1)):
        """Initialize queue listener handler.

        Args:
            handlers (list): List of handlers to process queued log records
            respect_handler_level (bool, optional): Whether to respect individual
                                                     handler log levels. Defaults to True.
            auto_run (bool, optional): Whether to automatically start the listener.
                                      Defaults to True.
            queue (Queue, optional): Queue for storing log records. Defaults to
                                    unlimited queue.
        """
        super().__init__(queue)
        handlers = _resolve_handlers(handlers)
        self._listener = QueueListener(
            self.queue,
            *handlers,
            respect_handler_level=respect_handler_level)
        if auto_run:
            self.start()
            register(self.stop)


    def start(self):
        """Start the queue listener thread."""
        self._listener.start()


    def stop(self):
        """Stop the queue listener thread."""
        self._listener.stop()


    def emit(self, record):
        """Emit a log record by putting it in the queue.

        Args:
            record: The log record to emit
        """
        return super().emit(record)