import logging
import sys
from contextvars import ContextVar

import structlog

from helpr.logging.config import LoggingConfig


class Logger:

    _log_context: ContextVar[dict] = ContextVar("log_context", default={})

    def __init__(self, level=logging.INFO):
        """Initialize logger with given name and level."""
        logging.getLogger().setLevel(level)  # Set base logger level
        logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)
        self.config = LoggingConfig()  # Create logging configuration
        structlog.configure(
            processors=self.config.processors,
            context_class=self.config.context_class,
            logger_factory=self.config.logger_factory,
            wrapper_class=structlog.make_filtering_bound_logger(level),
            cache_logger_on_first_use=True,
        )
        self.logger = structlog.get_logger()

    def set_log_context(self, **kwargs):
        current_context = self._log_context.get().copy()
        current_context.update(kwargs)
        self._log_context.set(current_context)

    def clear_log_context(self):
        self._log_context.set({})

    def get_log_context(self):
        return self._log_context.get()

    def info(self, message: str, **kwargs):
        self.logger.info(message, **self.get_log_context(), **kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, **self.get_log_context(), **kwargs, exc_info=True)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, **self.get_log_context(), **kwargs)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, **self.get_log_context(), **kwargs)
